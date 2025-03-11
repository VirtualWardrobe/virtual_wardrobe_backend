from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from prisma import Prisma
from typing import List, Optional
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
    category: str = Form(...),
    type: str = Form(...),
    brand: str = Form(...),
    size: str = Form(...),
    color: str = Form(...),
    userId: str = Form(...),
    image: Optional[UploadFile] = File(default=None),
    db: Prisma = Depends(get_prisma)
):
    user = await db.user.find_unique(where={"id": userId})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    image_data = None
    if image and image.file and image.size > 0:
        raw_bytes = await image.read()
        image_data = base64.b64encode(raw_bytes).decode("utf-8")

    data = {
        "category": category,
        "type": type,
        "brand": brand,
        "size": size,
        "color": color,
        "userId": userId,
        "image": image_data
    }

    try:
        created_item = await db.item.create(data=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create item: {str(e)}")

    response = {
        "id": created_item.id,
        "category": created_item.category,
        "type": created_item.type,
        "brand": created_item.brand,
        "size": created_item.size,
        "color": created_item.color,
        "userId": created_item.userId,
        "image": f"data:image/jpeg;base64,{created_item.image}" if created_item.image else None
    }
    return response


@router.get("/items", response_model=List[ItemResponse])
async def get_items(db: Prisma = Depends(get_prisma)):
    items = await db.item.find_many()
    result = []
    for item in items:
        item_dict = {
            "id": item.id,
            "category": item.category,
            "type": item.type,
            "brand": item.brand,
            "size": item.size,
            "color": item.color,
            "userId": item.userId,
            "image": f"data:image/jpeg;base64,{item.image}" if item.image else None
        }
        result.append(item_dict)
    return result


@router.get("/items/{item_id}", response_model=ItemResponse)
async def get_item(item_id: str, db: Prisma = Depends(get_prisma)):
    item = await db.item.find_unique(where={"id": item_id})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    response = {
        "id": item.id,
        "category": item.category,
        "type": item.type,
        "brand": item.brand,
        "size": item.size,
        "color": item.color,
        "userId": item.userId,
        "image": f"data:image/jpeg;base64,{item.image}" if item.image else None
    }
    return response


@router.put("/items/{item_id}", response_model=ItemResponse)
async def update_item(
    item_id: str,
    category: str = Form(...),
    type: str = Form(...),
    brand: str = Form(...),
    size: str = Form(...),
    color: str = Form(...),
    userId: str = Form(...),
    image: Optional[UploadFile] = File(default=None),
    db: Prisma = Depends(get_prisma)
):
    existing_item = await db.item.find_unique(where={"id": item_id})
    if not existing_item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    image_data = existing_item.image
    if image and image.file and image.size > 0:
        raw_bytes = await image.read()
        image_data = base64.b64encode(raw_bytes).decode("utf-8")

    updated_item = await db.item.update(
        where={"id": item_id},
        data={
            "category": category,
            "type": type,
            "brand": brand,
            "size": size,
            "color": color,
            "image": image_data
        }
    )

    response = {
        "id": updated_item.id,
        "category": updated_item.category,
        "type": updated_item.type,
        "brand": updated_item.brand,
        "size": updated_item.size,
        "color": updated_item.color,
        "userId": updated_item.userId,
        "image": f"data:image/jpeg;base64,{updated_item.image}" if updated_item.image else None
    }
    return response


@router.delete("/items/{item_id}", response_model=ItemResponse)
async def delete_item(item_id: str, db: Prisma = Depends(get_prisma)):
    existing_item = await db.item.find_unique(where={"id": item_id})
    if not existing_item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    deleted_item = await db.item.delete(where={"id": item_id})
    
    response = {
        "id": deleted_item.id,
        "category": deleted_item.category,
        "type": deleted_item.type,
        "brand": deleted_item.brand,
        "size": deleted_item.size,
        "color": deleted_item.color,
        "userId": deleted_item.userId,
        "image": f"data:image/jpeg;base64,{deleted_item.image}" if deleted_item.image else None
    }
    return response


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
