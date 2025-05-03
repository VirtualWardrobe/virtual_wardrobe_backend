import uuid, logging, re, httpx, anyio.to_thread, base64
from google.cloud import storage
from fastapi import status, HTTPException
from urllib.parse import urlparse, unquote
from typing import Optional, Tuple
from datetime import timedelta
from env import env


def decode(encoded_string: str) -> Optional[str]:
    """
    Decode a URL-safe base64 string back to original format.
    
    Args:
        encoded_string: The string to decode
        
    Returns:
        Decoded string or None if decoding fails
    """
    try:
        # Add padding back if needed
        padding_needed = len(encoded_string) % 4
        if padding_needed:
            encoded_string += '=' * (4 - padding_needed)
        
        # Convert to bytes and decode from URL-safe base64
        encoded_bytes = encoded_string.encode('ascii')
        decoded_bytes = base64.urlsafe_b64decode(encoded_bytes)
        
        # Convert back to string
        decoded_string = decoded_bytes.decode('utf-8')
        
        return decoded_string
        
    except Exception as e:
        logging.error(f"Error decoding string: {e}")
        return None


# Create service account configuration from environment variables
service_account_info = {
    "type": "service_account",
    "project_id": env.GCP_PROJECT_ID,
    "private_key_id": env.GCP_PRIVATE_KEY_ID,
    "private_key": f"-----BEGIN PRIVATE KEY-----\n{decode(env.GCP_PRIVATE_KEY)}\n-----END PRIVATE KEY-----\n",
    "client_email": env.GCP_CLIENT_EMAIL,
    "client_id": env.GCP_CLIENT_ID,
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": env.GCP_CLIENT_X509_CERT_URL,
    "universe_domain": "googleapis.com"
}


# Initialize Google Cloud Storage client
storage_client = storage.Client.from_service_account_info(service_account_info)

# Allowed file extensions
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "pdf", "webp", "svg", "mp3", "wav", "ogg", "aac"}

# storage_client = None


def is_allowed_file(filename: str) -> bool:
    """
    Check if the file has an allowed extension.
    """
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


async def upload_file_to_gcs(
    file: bytes, bucket_name: str, folder_name: Optional[str] = None, content_type: Optional[str] = None,
    filename: Optional[str] = None
) -> str:
    """
    Upload a file to the GCS bucket and return the uploaded file URL.
    If folder_name is provided, the file will be uploaded to that folder within the bucket.

    Args:
        file (bytes): The file content as bytes.
        bucket_name (str): The name of the GCS bucket.
        folder_name (Optional[str]): The folder name within the bucket (optional).
        content_type (Optional[str]): The MIME type of the file (e.g., "image/png", "audio/mpeg").
        filename (Optional[str]): The original filename to include in the uploaded object name (optional).

    Returns:
        str: The URL of the uploaded file.

    Raises:
        HTTPException: If the file type is invalid or an error occurs during upload.
    """
    try:
        bucket = storage_client.bucket(bucket_name)

        # Generate a unique name for the file
        unique_key = str(uuid.uuid4())
        
        # Include original filename if provided make sure its unique before passing it to this function
        if filename:
            object_key = f"{unique_key}/{filename}"
        else:
            object_key = unique_key

        # Construct the object name with folder path if provided
        if folder_name:
            folder_name = folder_name.strip("/")
            if not re.match(r"^[a-zA-Z0-9_\-/]+$", folder_name):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Folder name can only contain alphanumeric characters, hyphens, underscores, and forward slashes.",
                )
            object_name = f"{folder_name}/{object_key}"
        else:
            object_name = object_key

        # Create a blob and upload the file (wrapped in anyio)
        blob = bucket.blob(object_name)
        await anyio.to_thread.run_sync(lambda: blob.upload_from_string(file, content_type=content_type))

        # Generate and return the file URL
        file_url = f"https://storage.googleapis.com/{bucket_name}/{object_name}"
        return file_url

    except Exception as e:
        logging.error(f"Error uploading file to GCS: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading file to GCS: {str(e)}",
        )


async def upload_image_from_url(image_url: str, bucket_name: str) -> str:
    """
    Upload an image from a URL to the GCS bucket and return the uploaded file URL.

    Args:
        image_url (str): The URL of the image to upload.
        bucket_name (str): The name of the GCS bucket.

    Returns:
        str: The URL of the uploaded image.

    Raises:
        HTTPException: If the image cannot be fetched or uploaded.
    """
    try:
        # Fetch image from URL asynchronously with httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(image_url)
            if response.status_code != status.HTTP_200_OK:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Unable to fetch image from URL"
                )

            if not response.content:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No image content to upload",
                )

        # Upload to GCS (wrapped in anyio)
        file_url = await upload_file_to_gcs(  
            file=response.content,
            bucket_name=bucket_name,
            content_type="image/png",
        )
        return file_url

    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        logging.error(f"Error uploading image from URL: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading image from URL: {str(e)}",
        )


async def upload_audio_file_to_gcs(
    file: bytes, bucket_name: str, folder_name: Optional[str] = None, content_type: Optional[str] = None
) -> str:
    """
    Upload an audio file to the GCS bucket and return the uploaded file URL.

    Args:
        file (bytes): The audio file content as bytes.
        bucket_name (str): The name of the GCS bucket.
        folder_name (Optional[str]): The folder name within the bucket (optional).
        content_type (Optional[str]): The MIME type of the file (e.g., "audio/mpeg").

    Returns:
        str: The URL of the uploaded file.

    Raises:
        HTTPException: If the file type is invalid or an error occurs during upload.
    """
    try:
       # Validate the content type
        if content_type and not content_type.startswith("audio/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Only audio files are allowed.",
            )

        # Upload the file to GCS (now async)
        file_url = await upload_file_to_gcs(
            file=file,
            bucket_name=bucket_name,
            folder_name=folder_name,
            content_type=content_type,
        )
        return file_url

    except HTTPException as http_ex:
        logging.error(http_ex)
        raise http_ex
    
    except Exception as e:
        logging.error(f"Error uploading audio file to GCS: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading audio file to GCS: {str(e)}",
        )


async def delete_file_from_gcs(file_url: str, bucket_name: str) -> dict:
    """
    Delete a file from the GCS bucket using its URL.

    Args:
        file_url (str): The URL of the file to delete.
        bucket_name (str): The name of the GCS bucket.

    Returns:
        dict: A message indicating success or failure.

    Raises:
        HTTPException: If the file is not found or an error occurs during deletion.
    """
    try:
        # Parse the URL to extract the object key
        bucket_name, object_key = parse_gcs_url(file_url)

        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(object_key)

        # Check if blob exists (wrapped in anyio)
        exists = await anyio.to_thread.run_sync(blob.exists)
        if not exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="File not found in GCS"
            )

        # Delete the object (wrapped in anyio)
        await anyio.to_thread.run_sync(blob.delete)
        return {"message": "File deleted successfully"}

    except HTTPException as http_ex:
        logging.error(http_ex)
        raise http_ex
    
    except Exception as e:
        logging.error(f"Error deleting file from GCS: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting file from GCS: {str(e)}",
        )


def parse_gcs_url(gcs_url: str) -> Tuple[str, str]:
    """
    Parse a GCS URL to extract the bucket name and object key.

    Args:
        gcs_url (str): The GCS URL to parse.

    Returns:
        Tuple[str, str]: The bucket name and object key.

    Raises:
        ValueError: If the URL format is invalid.
    """
    try:
        # Clean the URL first
        gcs_url = unquote(gcs_url.split("?")[0])

        if gcs_url.startswith("gs://"):
            pattern = r"gs://([^/]+)/(.+)"
            match = re.match(pattern, gcs_url)
            if not match:
                raise ValueError("Invalid GCS URL format")
            return match.group(1), match.group(2)

        elif gcs_url.startswith("https://"):
            parsed_url = urlparse(gcs_url)
            path_parts = parsed_url.path.strip("/").split("/")

            if "storage.googleapis.com" in parsed_url.netloc:
                bucket_name = path_parts[0]
                object_key = "/".join(path_parts[1:])
                return bucket_name, object_key
            else:
                raise ValueError("Invalid GCS URL format")

        elif "/" in gcs_url:
            parts = gcs_url.strip("/").split("/")
            bucket_name = parts[0]
            object_key = "/".join(parts[1:])
            return bucket_name, object_key

        else:
            raise ValueError(
                "Invalid GCS URL format. Must be gs://, https://, or bucket/key format"
            )

    except Exception as e:
        logging.error(f"Error parsing GCS URL '{gcs_url}': {str(e)}")
        raise ValueError(f"Error parsing GCS URL: {str(e)}")


async def generate_signed_url(gcs_url: str, expires_in: int = 3600) -> str:
    """
    Generate a signed URL for a private GCS object using its GCS URL.

    Args:
        gcs_url (str): The GCS URL of the object.
        expires_in (int): The expiration time for the signed URL in seconds.

    Returns:
        str: The signed URL.

    Raises:
        HTTPException: If an error occurs during URL generation.
    """
    try:
        # Parse the URL to get bucket and key
        bucket_name, object_key = parse_gcs_url(gcs_url)

        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(object_key)

        # Generate signed URL (wrapped in anyio with lambda to handle kwargs)
        signed_url = await anyio.to_thread.run_sync(
            lambda: blob.generate_signed_url(
                version="v4",
                expiration=expires_in,
                method="GET"
            )
        )

        logging.info(f"Generated signed URL for {gcs_url}")
        return signed_url

    except Exception as e:
        logging.error(f"Error generating signed URL for {gcs_url}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


def is_gcs_url(url: str) -> bool:
    """
    Check if the URL is a GCS URL.

    Args:
        url (str): The URL to check.

    Returns:
        bool: True if the URL is a GCS URL, False otherwise.
    """
    if not url or len(url)==0:
        return False
    
    return "storage.googleapis.com" in url or url.startswith("gs://")


async def generate_pdf_upload_signed_url(
    bucket_name: str,
    filename: str,
    expires_in: int = 900,  # 15 minutes default expiration
) -> Tuple[str, str]:  # Adjusted return type to Tuple[str, str] for clarity
    """
    Generate a signed URL for uploading a PDF file to GCS.

    Args:
        bucket_name (str): The name of the GCS bucket.
        filename (str): The desired filename for the PDF (including .pdf extension).
        expires_in (int): Expiration time in seconds (default: 900 seconds = 15 minutes).

    Returns:
        Tuple[str, str]: The signed URL and the object name.

    Raises:
        HTTPException: If the filename is invalid or an error occurs.
    """
    try:
        if not is_allowed_file(filename) or not filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename. Only PDF files are allowed."
            )

        # Generate a unique object name to avoid conflicts
        unique_key = str(uuid.uuid4())
        object_name = f"{unique_key}_{filename}" if filename else unique_key

        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(object_name)

        # Generate signed URL for upload (wrapped in anyio with lambda to handle kwargs)
        signed_url = await anyio.to_thread.run_sync(
            lambda: blob.generate_signed_url(
                version="v4",
                expiration=timedelta(seconds=expires_in),
                method="PUT",
                content_type="application/pdf"
            )
        )

        logging.info(f"Generated signed URL for uploading PDF: {object_name}")
        return signed_url, object_name

    except Exception as e:
        logging.error(f"Error generating signed URL for PDF upload: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating signed URL: {str(e)}"
        )
