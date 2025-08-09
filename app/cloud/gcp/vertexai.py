from fastapi import HTTPException, status
from google.oauth2 import service_account
from env import env
import logging
import base64
import asyncio
from google import genai
from google.genai.types import RecontextImageSource, ProductImage, Image

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def decode(encoded_string: str) -> str:
    try:
        encoded_string += "=" * ((4 - len(encoded_string) % 4) % 4)
        return base64.urlsafe_b64decode(encoded_string.encode("ascii")).decode("utf-8")
    except Exception as e:
        logger.error("Failed to decode environment variable: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to decode private key from environment variables."
        )

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

# Define the required scope
scopes = ['https://www.googleapis.com/auth/cloud-platform']

# Pass the scope when creating credentials
credentials = service_account.Credentials.from_service_account_info(
    service_account_info,
    scopes=scopes
)

client = genai.Client(
    vertexai=True,
    credentials=credentials,
    project=env.GCP_PROJECT_ID,
    location="us-central1"
)

def encode_image_to_base64(file_bytes: bytes) -> str:
    return base64.b64encode(file_bytes).decode("utf-8")

async def run_virtual_tryon(human_bytes: bytes, garment_bytes: bytes):
    try:
        logger.info("Sending request to Vertex AI Virtual Try-on model...")

        response = await asyncio.to_thread(
            client.models.recontext_image,
            model="virtual-try-on-preview-08-04",
            source=RecontextImageSource(
                person_image=Image(image_bytes=human_bytes),
                product_images=[ProductImage(product_image=Image(image_bytes=garment_bytes))]
            ),
        )

        if not response.generated_images:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Vertex AI returned no generated images."
            )

        generated_image = response.generated_images[0].image
        image_bytes = generated_image.image_bytes
        
        return base64.b64encode(image_bytes).decode("utf-8")

    except HTTPException:
        raise

    except Exception as e:
        logger.error("Error calling Vertex AI Virtual Try-on: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calling Vertex AI: {str(e)}"
        )