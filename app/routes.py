from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from prisma import Prisma
from typing import List
from app.models import UserCreate, UserUpdate, UserResponse, ItemResponse, ContactCreate, ContactResponse
from app.prisma_client import PrismaClient
import base64


router = APIRouter()


async def get_prisma():
    prisma = await PrismaClient.get_instance()
    return prisma


@router.post("/users", response_model=UserResponse)
async def create_user(
    user: UserCreate,
    db: Prisma = Depends(get_prisma)
):
    existing_user = await db.user.find_first(
        where={"OR": [{"email": user.email}, {"username": user.username}]}
    )
    if existing_user:
        raise HTTPException(status_code=400, detail="Email or username already exists")
    
    created_user = await db.user.create(
        data=user.model_dump()
    )
    return created_user


@router.get("/users", response_model=List[UserResponse])
async def get_users(
    db: Prisma = Depends(get_prisma)
):
    users = await db.user.find_many()
    return users


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: Prisma = Depends(get_prisma)
):
    user = await db.user.find_unique(where={"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user: UserUpdate,
    db: Prisma = Depends(get_prisma)
):
    existing_user = await db.user.find_unique(where={"id": user_id})
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    updated_user = await db.user.update(
        where={"id": user_id},
        data=user.model_dump(exclude_unset=True)
    )
    return updated_user


@router.delete("/users/{user_id}", response_model=UserResponse)
async def delete_user(
    user_id: str,
    db: Prisma = Depends(get_prisma)
):
    existing_user = await db.user.find_unique(where={"id": user_id})
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    deleted_user = await db.user.delete(where={"id": user_id})
    return deleted_user


@router.post("/items", response_model=ItemResponse)
async def create_item(
    category: str,
    type: str,
    brand: str,
    size: str,
    color: str,
    userId: str,
    db: Prisma = Depends(get_prisma)
):
    user = await db.user.find_unique(where={"id": userId})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    created_item = await db.item.create(
        data={
            "category": category,
            "type": type,
            "brand": brand,
            "size": size,
            "color": color,
            "userId": userId
        }
    )

    return created_item


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
    category: str,
    type: str,
    brand: str,
    size: str,
    color: str,
    db: Prisma = Depends(get_prisma)
):
    existing_item = await db.item.find_unique(where={"id": item_id})
    if not existing_item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    updated_item = await db.item.update(
        where={"id": item_id},
        data={
            "category": category,
            "type": type,
            "brand": brand,
            "size": size,
            "color": color,
        }
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


@router.post("/contact", response_model=ContactCreate)
async def create_contact(
    contact: ContactCreate,
    db: Prisma = Depends(get_prisma)
):
    created_contact = await db.contact.create(
        data=contact.model_dump()
    )
    return created_contact


@router.get("/contact", response_model=List[ContactResponse])
async def get_contacts(
    db: Prisma = Depends(get_prisma)
):
    contacts = await db.contact.find_many()
    return contacts
