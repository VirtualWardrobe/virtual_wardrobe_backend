from fastapi import APIRouter, HTTPException, Depends
from prisma import Prisma
from typing import List
from app.items.models import ItemCreate, ItemUpdate, ItemResponse
from app.prisma_client import PrismaClient


router = APIRouter()


async def get_prisma():
    prisma = await PrismaClient.get_instance()
    return prisma


@router.post("/items")
async def create_items(
    items: List[ItemCreate],
    db: Prisma = Depends(get_prisma)
):
    created_items = await db.item.create_many(
        data=[item.model_dump(exclude_unset=True) for item in items]
    )
    
    if created_items:
        return {
            "success": True,
            "message": f"{created_items} items created successfully"
        }
    else:
        raise HTTPException(status_code=400, detail="Failed to create items")


@router.get("/items", response_model=List[ItemResponse])
async def get_items(
    db: Prisma = Depends(get_prisma)
):
    items = await db.item.find_many()
    return items


@router.get("/items/{item_id}", response_model=ItemResponse)
async def get_item(
    item_id: str,
    db: Prisma = Depends(get_prisma)
):
    item = await db.item.find_unique(where={"id": item_id})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.put("/items/{item_id}", response_model=ItemResponse)
async def update_item(
    item_id: str,
    item: ItemUpdate,
    db: Prisma = Depends(get_prisma)
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
    db: Prisma = Depends(get_prisma)
):
    existing_item = await db.item.find_unique(where={"id": item_id})
    if not existing_item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    deleted_item = await db.item.delete(where={"id": item_id})
    return deleted_item


@router.get("/users/{user_id}/items", response_model=List[ItemResponse])
async def get_user_items(
    user_id: str,
    db: Prisma = Depends(get_prisma)
):
    items = await db.item.find_many(where={"userId": user_id})
    return items
