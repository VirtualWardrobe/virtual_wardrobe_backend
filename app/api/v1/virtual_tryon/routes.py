from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from typing import Optional
from prisma import Prisma
from prisma.enums import ClothType
from app.db.prisma_client import get_prisma
from app.redis.redis_client import redis_handler
from app.api.v1.user.auth.routes.user import get_current_user
from app.cloud.gcp.storage import upload_file_to_gcs
from app.utils.success_handler import success_response
from env import env
import logging, fal_client, math, json


router = APIRouter()


@router.post("/virtual-tryon")
async def virtual_tryon(
    cloth_type: ClothType,
    human_image: UploadFile = File(...),
    garment_image: UploadFile = File(...),
    prisma: Prisma = Depends(get_prisma),
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

        async with prisma.tx(timeout=65000,max_wait=80000) as tx:
            result = await tx.virtualtryon.create(
                data=data
            )

            redis_client = await redis_handler.get_client()
            virtual_tryon_keys = await redis_client.keys(f'virtual_tryon_{user.id}_*')
            user_info_keys = await redis_client.keys(f'user_info_{user.id}')
            keys = virtual_tryon_keys + user_info_keys
            if keys:
                await redis_client.delete(*keys)

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
    prisma: Prisma = Depends(get_prisma),
    page: Optional[int] = Query(1, ge=1),
    page_size: Optional[int] = Query(10, ge=1, le=100),
    user=Depends(get_current_user)
):
    try:
        cache_key = f"virtual_tryon_{user.id}_{page}_{page_size}"
        redis_client = await redis_handler.get_client()
        cached_data = await redis_client.get(cache_key)
 
        if cached_data:
            return success_response(
                message="Virtual try-on results retrieved from cache",
                data=json.loads(cached_data)
            )

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

        serialized_data = [result.model_dump(mode='json') for result in results]
        
        response_data = {
            "items": serialized_data,
            "metadata": {
                "page": page,
                "page_size": page_size,
                "total_items": total_count,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1
            }
        }

        await redis_client.setex(cache_key, 3600, json.dumps(response_data))
        
        return success_response(
            message="Virtual try-on results retrieved successfully",
            data=response_data
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
    prisma: Prisma = Depends(get_prisma),
    user=Depends(get_current_user)
):
    try:
        cache_key = f"virtual_tryon_{user.id}_{tryon_id}"
        redis_client = await redis_handler.get_client()
        cached_data = await redis_client.get(cache_key)

        if cached_data:
            return success_response(
                message="Virtual try-on result retrieved from cache",
                data=json.loads(cached_data)
            )
        
        result = await prisma.virtualtryon.find_first(
            where={
                "id": tryon_id,
                "user_id": user.id
            }
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="Virtual try-on result not found")
        
        result_dict = result.model_dump(mode='json')
        await redis_client.setex(cache_key, 3600, json.dumps(result_dict))
        
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
