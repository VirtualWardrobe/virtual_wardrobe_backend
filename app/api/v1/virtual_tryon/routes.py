from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from typing import Optional
from prisma import Prisma
from prisma.enums import ClothType
from app.db.prisma_client import PrismaClient
from app.api.v1.user.auth.routes.user import get_current_user
from app.cloud.gcp.storage import upload_file_to_gcs
from app.utils.success_handler import success_response
from env import env
import logging, fal_client, math


router = APIRouter()


@router.post("/virtual-tryon")
async def virtual_tryon(
    cloth_type: ClothType,
    human_image: UploadFile = File(...),
    garment_image: UploadFile = File(...),
    prisma: Prisma = Depends(PrismaClient.get_instance),
    user=Depends(get_current_user)
):
    try:
        data = {
            "user_id": user.id,
            "cloth_type": cloth_type
        }

        file_name = human_image.filename
        file_content = await human_image.read()
        human_image_url = await upload_file_to_gcs(
            file=file_content,
            bucket_name=env.GOOGLE_STORAGE_MEDIA_BUCKET,
            folder_name="virtual-tryon/human",
            content_type=human_image.content_type,
            filename=file_name
        )
        data["human_image_url"] = human_image_url

        file_name = garment_image.filename
        file_content = await garment_image.read()
        garment_image_url = await upload_file_to_gcs(
            file=file_content,
            bucket_name=env.GOOGLE_STORAGE_MEDIA_BUCKET,
            folder_name="virtual-tryon/garment",
            content_type=garment_image.content_type,
            filename=file_name
        )
        data["garment_image_url"] = garment_image_url
        
        result_image = fal_client.subscribe(
            "fal-ai/cat-vton",
            arguments={
                "human_image_url": human_image_url,
                "garment_image_url": garment_image_url,
                "cloth_type": cloth_type.lower()
            },
            with_logs=True
        )
        data["result_image_url"] = result_image["image"]["url"]

        result = await prisma.virtualtryon.create(
            data=data
        )

        return success_response(
            message="Virtual try-on finished successfully",
            data=result
        )
    
    except HTTPException as httpx:
        logging.error(httpx)
        raise httpx
    
    except Exception as e:
        logging.error(f"Error occurred during virtual try-on: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/virtual-tryon")
async def get_virtual_tryon(
    prisma: Prisma = Depends(PrismaClient.get_instance),
    page: Optional[int] = Query(1, ge=1),
    page_size: Optional[int] = Query(10, ge=1, le=100),
    user=Depends(get_current_user)
):
    try:
        skip = (page - 1) * page_size
        
        filters = {
            "user_id": user.id
        }

        results = await prisma.virtualtryon.find_many(
            where=filters,
            skip=skip,
            take=page_size,
            order={"created_at": "desc"}
        )
        
        total_count = await prisma.virtualtryon.count(where=filters)
        total_pages = math.ceil(total_count / page_size)
        
        return success_response(
            message="Virtual try-on results retrieved successfully",
            data={
                "items": results,
                "metadata": {
                    "page": page,
                    "page_size": page_size,
                    "total_items": total_count,
                    "total_pages": total_pages,
                    "has_next": page < total_pages,
                    "has_previous": page > 1
                }
            }
        )
    
    except HTTPException as httpx:
        logging.error(httpx)
        raise httpx
    
    except Exception as e:
        logging.error(f"Error retrieving virtual try-on results: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/virtual-tryon/{tryon_id}")
async def get_virtual_tryon_by_id(
    tryon_id: str,
    prisma: Prisma = Depends(PrismaClient.get_instance),
    user=Depends(get_current_user)
):
    try:
        result = await prisma.virtualtryon.find_first(
            where={
                "id": tryon_id,
                "user_id": user.id
            }
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="Virtual try-on result not found")
        
        return success_response(
            message="Virtual try-on result retrieved successfully",
            data=result
        )
    
    except HTTPException as httpx:
        logging.error(httpx)
        raise httpx
    
    except Exception as e:
        logging.error(f"Error retrieving virtual try-on result: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
