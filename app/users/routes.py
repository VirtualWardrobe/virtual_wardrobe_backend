from fastapi import APIRouter, HTTPException, Depends
from prisma import Prisma
from typing import List
from app.users.models import UserCreate, UserUpdate, UserResponse
from app.prisma_client import PrismaClient


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
    
    await db.item.delete_many(where={"userId": user_id})
    deleted_user = await db.user.delete(
        where={"id": user_id}
    )
    return deleted_user
