from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from prisma import Prisma
from typing import List
from app.models import UserCreate, UserResponse, ItemResponse
from app.prisma_client import PrismaClient
import base64


router = APIRouter()


async def get_prisma() -> Prisma:
    prisma = await PrismaClient.get_instance()
    return prisma


@router.post("/users", response_model=UserResponse)
async def create_user(user: UserCreate, db: Prisma = Depends(get_prisma)):
    existing_user = await db.user.find_first(
        where={"OR": [{"email": user.email}, {"username": user.username}]}
    )
    if existing_user:
        raise HTTPException(status_code=400, detail="Email or username already exists")
    
    created_user = await db.user.create(
        data=user.model_dump()
    )
    return created_user


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, db: Prisma = Depends(get_prisma)):
    user = await db.user.find_unique(where={"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/users", response_model=List[UserResponse])
async def get_users(db: Prisma = Depends(get_prisma)):
    users = await db.user.find_many()
    return users


@router.post("/items", response_model=ItemResponse)
async def create_item(
    category: str,
    type: str,
    brand: str,
    size: str,
    color: str,
    userId: str,
    image: UploadFile = File(...),
    db: Prisma = Depends(get_prisma)
):
    user = await db.user.find_unique(where={"id": userId})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    image_data = await image.read()

    created_item = await db.item.create(
        data={
            "category": category,
            "type": type,
            "brand": brand,
            "size": size,
            "color": color,
            "image": image_data,
            "userId": userId
        }
    )

    return {
        "id": created_item.id,
        "category": created_item.category,
        "type": created_item.type,
        "brand": created_item.brand,
        "size": created_item.size,
        "color": created_item.color,
        "image": base64.b64encode(created_item.image).decode('utf-8') if created_item.image else None,
        "userId": created_item.userId
    }


@router.get("/items/{item_id}", response_model=ItemResponse)
async def get_item(item_id: str, db: Prisma = Depends(get_prisma)):
    item = await db.item.find_unique(where={"id": item_id})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return {
        "id": item.id,
        "category": item.category,
        "type": item.type,
        "brand": item.brand,
        "size": item.size,
        "color": item.color,
        "image": base64.b64encode(item.image).decode('utf-8') if item.image else None,
        "userId": item.userId
    }


@router.get("/users/{user_id}/items", response_model=List[ItemResponse])
async def get_user_items(user_id: str, db: Prisma = Depends(get_prisma)):
    items = await db.item.find_many(where={"userId": user_id})
    return [
        {
            "id": item.id,
            "category": item.category,
            "type": item.type,
            "brand": item.brand,
            "size": item.size,
            "color": item.color,
            "image": base64.b64encode(item.image).decode('utf-8') if item.image else None,
            "userId": item.userId
        }
        for item in items
    ]
