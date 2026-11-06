import asyncio
import base64
import json
import logging
from typing import Any

import boto3
from fastapi import HTTPException, status

from env import env

logger = logging.getLogger(__name__)

MODEL_ID = "amazon.nova-canvas-v1:0"


def _create_bedrock_runtime_client():
    client_kwargs: dict[str, Any] = {"region_name": env.AWS_REGION}
    if env.AWS_ACCESS_KEY_ID and env.AWS_SECRET_ACCESS_KEY:
        client_kwargs.update(
            {
                "aws_access_key_id": env.AWS_ACCESS_KEY_ID,
                "aws_secret_access_key": env.AWS_SECRET_ACCESS_KEY,
            }
        )
        if env.AWS_SESSION_TOKEN:
            client_kwargs["aws_session_token"] = env.AWS_SESSION_TOKEN
    return boto3.client("bedrock-runtime", **client_kwargs)


def _build_payload(
    human_bytes: bytes, garment_bytes: bytes, garment_type: str
) -> dict[str, Any]:
    return {
        "taskType": "VIRTUAL_TRY_ON",
        "virtualTryOnParams": {
            "sourceImage": base64.b64encode(human_bytes).decode("utf-8"),
            "referenceImage": base64.b64encode(garment_bytes).decode("utf-8"),
            "maskType": "GARMENT",
            "garmentBasedMask": {
                "garmentClass": garment_type,
            },
        },
        "imageGenerationConfig": {
            "numberOfImages": 1,
            "quality": "standard",
            "cfgScale": 8.0,
        },
    }


def _invoke_nova(
    human_bytes: bytes, garment_bytes: bytes, garment_type: str
) -> str:
    response = _create_bedrock_runtime_client().invoke_model(
        modelId=MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(
            _build_payload(human_bytes, garment_bytes, garment_type)
        ),
    )
    response_body = json.loads(response["body"].read())
    generated_images = response_body.get("images", [])
    if not generated_images:
        raise RuntimeError("Amazon Nova returned no generated images.")
    return generated_images[0]


async def run_virtual_tryon(
    human_bytes: bytes, garment_bytes: bytes, garment_type: str = "UPPER_BODY"
) -> str:
    try:
        logger.info("Sending request to Amazon Nova Canvas Virtual Try-on model...")
        return await asyncio.to_thread(
            _invoke_nova, human_bytes, garment_bytes, garment_type
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error calling Amazon Nova Canvas Virtual Try-on: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calling Amazon Nova Canvas: {e}",
        ) from e
