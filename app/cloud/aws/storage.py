import logging
import re
import uuid
from typing import Optional, Tuple
from urllib.parse import unquote, urlparse

import anyio.to_thread
import httpx
from fastapi import HTTPException, status

import boto3
from botocore.exceptions import ClientError

from env import env


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "gif",
    "pdf",
    "webp",
    "svg",
    "mp3",
    "wav",
    "ogg",
    "aac",
}


def _create_s3_client():
    client_kwargs = {"region_name": env.AWS_REGION}
    if env.AWS_ACCESS_KEY_ID and env.AWS_SECRET_ACCESS_KEY:
        client_kwargs.update(
            {
                "aws_access_key_id": env.AWS_ACCESS_KEY_ID,
                "aws_secret_access_key": env.AWS_SECRET_ACCESS_KEY,
            }
        )
        if env.AWS_SESSION_TOKEN:
            client_kwargs["aws_session_token"] = env.AWS_SESSION_TOKEN
    return boto3.client("s3", **client_kwargs)


s3_client = _create_s3_client()


def is_allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _object_url(bucket_name: str, object_key: str) -> str:
    region = env.AWS_REGION
    endpoint = (
        f"https://{bucket_name}.s3.amazonaws.com"
        if region == "us-east-1"
        else f"https://{bucket_name}.s3.{region}.amazonaws.com"
    )
    return f"{endpoint}/{object_key}"


async def upload_file_to_s3(
    file: bytes,
    bucket_name: str,
    folder_name: Optional[str] = None,
    content_type: Optional[str] = None,
    filename: Optional[str] = None,
) -> str:
    try:
        unique_key = str(uuid.uuid4())
        object_key = f"{unique_key}/{filename}" if filename else unique_key

        if folder_name:
            folder_name = folder_name.strip("/")
            if not re.match(r"^[a-zA-Z0-9_\-/]+$", folder_name):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Folder name can only contain alphanumeric characters, hyphens, underscores, and forward slashes.",
                )
            object_key = f"{folder_name}/{object_key}"

        put_kwargs = {
            "Bucket": bucket_name,
            "Key": object_key,
            "Body": file,
        }
        if content_type:
            put_kwargs["ContentType"] = content_type

        await anyio.to_thread.run_sync(lambda: s3_client.put_object(**put_kwargs))
        return _object_url(bucket_name, object_key)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error uploading file to S3: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading file to S3: {str(e)}",
        )


async def upload_image_from_url(image_url: str, bucket_name: str) -> str:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(image_url)
            if response.status_code != status.HTTP_200_OK:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Unable to fetch image from URL",
                )
            if not response.content:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No image content to upload",
                )

        return await upload_file_to_s3(
            file=response.content,
            bucket_name=bucket_name,
            content_type="image/png",
        )
    except HTTPException as http_ex:
        logger.error("HTTP error while uploading image from URL: %s", http_ex)
        raise
    except Exception as e:
        logger.error("Error uploading image from URL: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading image from URL: {str(e)}",
        )


async def upload_audio_file_to_s3(
    file: bytes,
    bucket_name: str,
    folder_name: Optional[str] = None,
    content_type: Optional[str] = None,
) -> str:
    try:
        if content_type and not content_type.startswith("audio/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Only audio files are allowed.",
            )
        return await upload_file_to_s3(
            file=file,
            bucket_name=bucket_name,
            folder_name=folder_name,
            content_type=content_type,
        )
    except HTTPException as http_ex:
        logger.error("HTTP error while uploading audio file: %s", http_ex)
        raise
    except Exception as e:
        logger.error("Error uploading audio file to S3: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading audio file to S3: {str(e)}",
        )


async def delete_file_from_s3(file_url: str, bucket_name: str) -> dict:
    try:
        parsed_bucket, object_key = parse_s3_url(file_url)
        bucket_name = parsed_bucket
        await anyio.to_thread.run_sync(
            lambda: s3_client.head_object(Bucket=bucket_name, Key=object_key)
        )
        await anyio.to_thread.run_sync(
            lambda: s3_client.delete_object(Bucket=bucket_name, Key=object_key)
        )
        return {"message": "File deleted successfully"}
    except HTTPException as http_ex:
        logger.error("HTTP error while deleting file from S3: %s", http_ex)
        raise
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")
        if error_code in {"404", "NoSuchKey", "NotFound"}:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="File not found in S3"
            )
        logger.error("Error deleting file from S3: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting file from S3: {str(e)}",
        )
    except Exception as e:
        logger.error("Error deleting file from S3: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting file from S3: {str(e)}",
        )


def parse_s3_url(s3_url: str) -> Tuple[str, str]:
    try:
        s3_url = unquote(s3_url.split("?", 1)[0])
        if s3_url.startswith("s3://"):
            match = re.match(r"s3://([^/]+)/(.+)", s3_url)
            if not match:
                raise ValueError("Invalid S3 URL format")
            return match.group(1), match.group(2)

        if s3_url.startswith("https://"):
            parsed_url = urlparse(s3_url)
            host = parsed_url.netloc.split(":", 1)[0]
            path = parsed_url.path.strip("/")
            if host.endswith(".amazonaws.com"):
                host_parts = host.split(".")
                if host_parts[0] == "s3":
                    parts = path.split("/", 1)
                    if len(parts) != 2:
                        raise ValueError("Invalid S3 URL format")
                    return parts[0], parts[1]
                bucket_name = host_parts[0]
                if path:
                    return bucket_name, path
            raise ValueError("Invalid S3 URL format")

        if "/" in s3_url:
            parts = s3_url.strip("/").split("/", 1)
            return parts[0], parts[1]
        raise ValueError("Invalid S3 URL format")
    except Exception as e:
        logger.error("Error parsing S3 URL '%s': %s", s3_url, str(e))
        raise ValueError(f"Error parsing S3 URL: {str(e)}")


def is_s3_url(url: str) -> bool:
    return bool(url) and ("amazonaws.com" in url or url.startswith("s3://"))


async def generate_signed_url(s3_url: str, expires_in: int = 3600) -> str:
    try:
        bucket_name, object_key = parse_s3_url(s3_url)
        return await anyio.to_thread.run_sync(
            lambda: s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket_name, "Key": object_key},
                ExpiresIn=expires_in,
            )
        )
    except Exception as e:
        logger.error("Error generating signed URL for %s: %s", s3_url, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


async def generate_pdf_upload_signed_url(
    bucket_name: str, filename: str, expires_in: int = 900
) -> Tuple[str, str]:
    try:
        if not is_allowed_file(filename) or not filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename. Only PDF files are allowed.",
            )

        object_key = f"{uuid.uuid4()}_{filename}"
        signed_url = await anyio.to_thread.run_sync(
            lambda: s3_client.generate_presigned_url(
                "put_object",
                Params={
                    "Bucket": bucket_name,
                    "Key": object_key,
                    "ContentType": "application/pdf",
                },
                ExpiresIn=expires_in,
            )
        )
        logger.info("Generated signed URL for uploading PDF: %s", object_key)
        return signed_url, object_key
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error generating signed URL for PDF upload: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating signed URL: {str(e)}",
        )
