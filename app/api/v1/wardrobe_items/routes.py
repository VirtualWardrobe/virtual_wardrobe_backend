from fastapi import APIRouter, HTTPException, Depends
from prisma import Prisma
from typing import List
from app.api.v1.wardrobe_items.models import ItemCreate, ItemResponse, ItemUpdate
from app.db.prisma_client import PrismaClient
import logging


router = APIRouter()


@router.post("/items")
async def create_items(
    items: List[ItemCreate],
    db: Prisma = Depends(PrismaClient.get_instance)
):
    try:
        items_data = []
        for item in items:
            data = item.model_dump(exclude_unset=True)
            items_data.append(data)

        created_items = await db.item.create_many(
            data=items_data
        )
        
        return {
            "success": True,
            "count": created_items,
            "items": items_data
        }
    
    except HTTPException as httpx:
        logging.error(httpx)
        raise httpx
    
    except Exception as e:
        logging.error(f"Error creating items: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/items", response_model=List[ItemResponse])
async def get_items(
    db: Prisma = Depends(PrismaClient.get_instance)
):
    items = await db.item.find_many()
    return items


@router.get("/items/{item_id}", response_model=ItemResponse)
async def get_item(
    item_id: str,
    db: Prisma = Depends(PrismaClient.get_instance)
):
    item = await db.item.find_unique(where={"id": item_id})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.put("/items/{item_id}", response_model=ItemResponse)
async def update_item(
    item_id: str,
    item: ItemUpdate,
    db: Prisma = Depends(PrismaClient.get_instance)
):
    existing_item = await db.item.find_unique(where={"id": item_id})
    if not existing_item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    updated_item = await db.item.update(
        where={"id": item_id},
        data=item.model_dump(exclude_unset=True)
    )
    return updated_item


@router.delete("/items/{item_id}", response_model=ItemResponse)
async def delete_item(
    item_id: str,
    db: Prisma = Depends(PrismaClient.get_instance)
):
    existing_item = await db.item.find_unique(where={"id": item_id})
    if not existing_item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    deleted_item = await db.item.delete(where={"id": item_id})
    return deleted_item


@router.get("/items/by-user/{user_id}", response_model=List[ItemResponse])
async def get_user_items(
    user_id: str,
    db: Prisma = Depends(PrismaClient.get_instance)
):
    items = await db.item.find_many(where={"userId": user_id})
    return items
