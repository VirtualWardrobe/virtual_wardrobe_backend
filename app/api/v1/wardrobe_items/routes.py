from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from typing import Optional
from prisma import Prisma
from prisma.enums import ItemCategory, ItemType, Size, Color
from app.db.prisma_client import PrismaClient
from app.api.v1.user.auth.routes.user import get_current_user
from app.cloud.gcp.storage import upload_file_to_gcs, delete_file_from_gcs
from app.utils.success_handler import success_response
from env import env
import logging, math


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
        data = {}
        data["user_id"] = user.id
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
        
        item = await prisma.wardrobeitem.create(data=data)
        return success_response(
            message="Wardrobe item created successfully",
            data=item
        )
    
    except HTTPException as httpx:
        logging.error(httpx)
        raise httpx
    
    except Exception as e:
        logging.error(f"Error creating wardrobe item: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/wardrobe-items")
async def get_wardrobe_items(
    prisma: Prisma = Depends(PrismaClient.get_instance),
    page: Optional[int] = Query(1, ge=1),
    page_size: Optional[int] = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    category: Optional[ItemCategory] = None,
    type: Optional[ItemType] = None,
    brand: Optional[str] = None,
    size: Optional[Size] = None,
    color: Optional[Color] = None,
    user=Depends(get_current_user),
):
    try:
        skip = (page - 1) * page_size
        
        filters = {
            "user_id": user.id
        }
        if category:
            filters["category"] = category
        if type:
            filters["type"] = type
        if brand:
            filters["brand"] = brand
        if size:
            filters["size"] = size
        if color:
            filters["color"] = color
        if search:
            filters["brand"] = {"contains": search, "mode": "insensitive"}
        
        items = await prisma.wardrobeitem.find_many(
            where=filters,
            skip=skip,
            take=page_size,
            order={"created_at": "desc"}
        )
        
        total_count = await prisma.wardrobeitem.count(where=filters)
        total_pages = math.ceil(total_count / page_size)
        
        return success_response(
            message="Wardrobe items retrieved successfully",
            data={
                "items": items,
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
        logging.error(f"Error retrieving wardrobe items: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get("/wardrobe-items/{item_id}")
async def get_wardrobe_item_by_id(
    item_id: str,
    prisma: Prisma = Depends(PrismaClient.get_instance),
    user=Depends(get_current_user)
):
    try:
        item = await prisma.wardrobeitem.find_first(
            where={
                "id": item_id,
                "user_id": user.id
            }
        )
        
        if not item:
            raise HTTPException(status_code=404, detail="Wardrobe item not found")
        
        return success_response(
            message="Wardrobe item retrieved successfully",
            data=item
        )
    
    except HTTPException as httpx:
        logging.error(httpx)
        raise httpx
    
    except Exception as e:
        logging.error(f"Error retrieving wardrobe item: {e}", exc_info=True)
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
        
        item = await prisma.wardrobeitem.update(
            where={
                "id": item_id,
                "user_id": user.id
            },
            data=data
        )
        
        return success_response(
            message="Wardrobe item updated successfully",
            data=item
        )
    
    except HTTPException as httpx:
        logging.error(httpx)
        raise httpx
    
    except Exception as e:
        logging.error(f"Error updating wardrobe item: {e}", exc_info=True)
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
        
        await delete_file_from_gcs(
            file_url=existing_item.image_url,
            bucket_name=env.GOOGLE_STORAGE_MEDIA_BUCKET
        )
        
        deleted_item = await prisma.wardrobeitem.delete(
            where={
                "id": item_id,
                "user_id": user.id
            }
        )
        
        return success_response(
            message="Wardrobe item deleted successfully",
            data=deleted_item.id
        )
    
    except HTTPException as httpx:
        logging.error(httpx)
        raise httpx
    
    except Exception as e:
        logging.error(f"Error deleting wardrobe item: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
