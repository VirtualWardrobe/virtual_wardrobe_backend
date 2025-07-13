from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from typing import Optional
from prisma import Prisma
from prisma.enums import ItemCategory, ItemType, Size, Color
from app.db.prisma_client import PrismaClient
from app.redis.redis_client import redis_handler
from app.api.v1.user.auth.routes.user import get_current_user
from app.cloud.gcp.storage import upload_file_to_gcs, delete_file_from_gcs
from app.utils.success_handler import success_response
from env import env
import logging, math, json


router = APIRouter()


@router.post("/wardrobe-items")
async def create_wardrobe_items(
    item_category: ItemCategory,
    item_type: Optional[ItemType] = None,
    item_brand: Optional[str] = None,
    item_size: Optional[Size] = None,
    item_color: Optional[Color] = None,
    image: Optional[UploadFile] = File(None),
    prisma: Prisma = Depends(PrismaClient.get_instance),
    user=Depends(get_current_user)
):
    try:
        data = {
            "user_id": user.id,
            "category": item_category
        }
        if item_type:
            data["type"] = item_type
        if item_brand:
            data["brand"] = item_brand
        if item_size:
            data["size"] = item_size
        if item_color:
            data["color"] = item_color
        if image:
            file_name = image.filename
            file_content = await image.read()
            file_url = await upload_file_to_gcs(
                file=file_content,
                bucket_name=env.GOOGLE_STORAGE_MEDIA_BUCKET,
                folder_name="wardrobe-items",
                content_type=image.content_type,
                filename=file_name
            )
            data["image_url"] = file_url

        async with prisma.tx(timeout=65000, max_wait=80000) as tx:
            item = await tx.wardrobeitem.create(data=data)
            redis_client = await redis_handler.get_client()
            keys = await redis_client.keys(f'wardrobe_items_{user.id}_*')
            if keys:
                await redis_client.delete(*keys)

        return success_response(
            message="Wardrobe item created successfully",
            data=item
        )

    except HTTPException as httpx:
        logging.error("HTTP error while creating wardrobe item: %s", httpx)
        raise httpx

    except Exception as e:
        logging.error("Error creating wardrobe item: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/wardrobe-items')
async def get_wardrobe_items(
    prisma: Prisma = Depends(PrismaClient.get_instance),
    page: Optional[int] = Query(1, ge=1),
    page_size: Optional[int] = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    category: Optional[ItemCategory] = None,
    item_type: Optional[ItemType] = None,
    brand: Optional[str] = None,
    size: Optional[Size] = None,
    color: Optional[Color] = None,
    user=Depends(get_current_user),
):
    try:
        skip = (page - 1) * page_size
        cache_key = f'wardrobe_items_{user.id}_{page}_{page_size}_{search}_{category}_{item_type}_{brand}_{size}_{color}'
        redis_client = await redis_handler.get_client()
        cached_data = await redis_client.get(cache_key)

        if cached_data:
            return success_response(
                message='Wardrobe items retrieved from cache',
                data=json.loads(cached_data)
            )

        filters = {
            'user_id': user.id
        }
        if category:
            filters['category'] = category
        if item_type:
            filters['type'] = item_type
        if brand:
            filters['brand'] = brand
        if size:
            filters['size'] = size
        if color:
            filters['color'] = color
        if search:
            filters['brand'] = {'contains': search, 'mode': 'insensitive'}

        items = await prisma.wardrobeitem.find_many(
            where=filters,
            skip=skip,
            take=page_size,
            order={'created_at': 'desc'}
        )

        total_count = await prisma.wardrobeitem.count(where=filters)
        total_pages = max(1, math.ceil(total_count / page_size))

        serializable_items = [item.model_dump(mode='json') for item in items]

        response_data = {
            'items': serializable_items,
            'metadata': {
                'page': page,
                'page_size': page_size,
                'total_items': total_count,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_previous': page > 1
            }
        }

        await redis_client.setex(cache_key, 3600, json.dumps(response_data))

        return success_response(
            message='Wardrobe items retrieved successfully',
            data=response_data
        )

    except HTTPException as httpx:
        logging.error("HTTP error while retrieving wardrobe items: %s", httpx)
        raise httpx

    except Exception as e:
        logging.error("Error retrieving wardrobe items: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/wardrobe-items/{item_id}")
async def get_wardrobe_item_by_id(
    item_id: str,
    prisma: Prisma = Depends(PrismaClient.get_instance),
    user=Depends(get_current_user)
):
    try:
        cache_key = f"wardrobe_item_{user.id}_{item_id}"
        redis_client = await redis_handler.get_client()
        cached_item = await redis_client.get(cache_key)

        if cached_item:
            return success_response(
                message="Wardrobe item retrieved from cache",
                data=json.loads(cached_item)
            )

        item = await prisma.wardrobeitem.find_first(
            where={
                "id": item_id,
                "user_id": user.id
            }
        )

        if not item:
            raise HTTPException(status_code=404, detail="Wardrobe item not found")

        item_dict = item.model_dump(mode='json')
        await redis_client.setex(cache_key, 3600, json.dumps(item_dict))

        return success_response(
            message="Wardrobe item retrieved successfully",
            data=item
        )

    except HTTPException as httpx:
        logging.error("HTTP error while retrieving wardrobe item: %s", httpx)
        raise httpx

    except Exception as e:
        logging.error("Error retrieving wardrobe item: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/wardrobe-items/{item_id}")
async def update_wardrobe_item(
    item_id: str,
    item_category: Optional[ItemCategory] = None,
    item_type: Optional[ItemType] = None,
    item_brand: Optional[str] = None,
    item_size: Optional[Size] = None,
    item_color: Optional[Color] = None,
    image: Optional[UploadFile] = File(None),
    prisma: Prisma = Depends(PrismaClient.get_instance),
    user=Depends(get_current_user)
):
    try:
        existing_item = await prisma.wardrobeitem.find_first(
            where={
                "id": item_id,
                "user_id": user.id
            }
        )

        if not existing_item:
            raise HTTPException(status_code=404, detail="Wardrobe item not found")

        data = {}
        if item_category:
            data["category"] = item_category
        if item_type:
            data["type"] = item_type
        if item_brand:
            data["brand"] = item_brand
        if item_size:
            data["size"] = item_size
        if item_color:
            data["color"] = item_color

        if image:
            await delete_file_from_gcs(
                file_url=existing_item.image_url,
                bucket_name=env.GOOGLE_STORAGE_MEDIA_BUCKET
            )
            file_name = image.filename
            file_content = await image.read()
            file_url = await upload_file_to_gcs(
                file=file_content,
                bucket_name=env.GOOGLE_STORAGE_MEDIA_BUCKET,
                folder_name="wardrobe-items",
                content_type=image.content_type,
                filename=file_name
            )
            data["image_url"] = file_url

        async with prisma.tx(timeout=65000, max_wait=80000) as tx:
            item = await tx.wardrobeitem.update(
                where={
                    "id": item_id,
                    "user_id": user.id
                },
                data=data
            )

            redis_client = await redis_handler.get_client()
            keys = await redis_client.keys(f'wardrobe_items_{user.id}_*')
            if keys:
                await redis_client.delete(*keys)

        return success_response(
            message="Wardrobe item updated successfully",
            data=item
        )

    except HTTPException as httpx:
        logging.error("HTTP error while updating wardrobe item: %s", httpx)
        raise httpx

    except Exception as e:
        logging.error("Error updating wardrobe item: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/wardrobe-items/{item_id}")
async def delete_wardrobe_item(
    item_id: str,
    prisma: Prisma = Depends(PrismaClient.get_instance),
    user=Depends(get_current_user)
):
    try:
        existing_item = await prisma.wardrobeitem.find_first(
            where={
                "id": item_id,
                "user_id": user.id
            }
        )

        if not existing_item:
            raise HTTPException(status_code=404, detail="Wardrobe item not found")

        if existing_item.image_url:
            await delete_file_from_gcs(
                file_url=existing_item.image_url,
                bucket_name=env.GOOGLE_STORAGE_MEDIA_BUCKET
            )

        async with prisma.tx(timeout=65000, max_wait=80000) as tx:
            deleted_item = await tx.wardrobeitem.delete(
                where={
                    "id": item_id,
                    "user_id": user.id
                }
            )

            redis_client = await redis_handler.get_client()
            keys = await redis_client.keys(f'wardrobe_items_{user.id}_*')
            if keys:
                await redis_client.delete(*keys)

        return success_response(
            message="Wardrobe item deleted successfully",
            data=deleted_item.id
        )

    except HTTPException as httpx:
        logging.error("HTTP error while deleting wardrobe item: %s", httpx)
        raise httpx

    except Exception as e:
        logging.error("Error deleting wardrobe item: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
