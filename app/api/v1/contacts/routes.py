from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from prisma import Prisma
from app.api.v1.contacts.models import Contact
from app.api.v1.user.auth.routes.user import get_current_user
from app.utils.success_handler import success_response
from app.db.prisma_client import get_prisma
import logging, math


router = APIRouter()


@router.post("/contacts")
async def create_contact(
    contact: Contact,
    prisma: Prisma = Depends(get_prisma),
    user = Depends(get_current_user)
):
    try:
        data = contact.model_dump(exclude_unset=True)

        created_contact = await prisma.contact.create(
            data=data
        )

        return success_response(
            message="Message sent successfully",
            data=created_contact
        )
    
    except HTTPException as httpx:
        logging.error("HTTPException: %s", httpx)
        raise httpx

    except Exception as e:
        logging.error("Error in sending message: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/contacts")
async def get_contacts(
    prisma: Prisma = Depends(get_prisma),
    page: Optional[int] = Query(1, ge=1),
    page_size: Optional[int] = Query(10, ge=1, le=100),
    user = Depends(get_current_user)
):
    try:
        skip = (page - 1) * page_size
        
        contacts = await prisma.contact.find_many(
            skip=skip,
            take=page_size
        )
        
        total_count = await prisma.contact.count()
        total_pages = math.ceil(total_count / page_size)
        
        return success_response(
            message="Messages retrieved successfully",
            data={
                "items": contacts,
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
        logging.error("HTTPException: %s", httpx)
        raise httpx

    except Exception as e:
        logging.error("Error in retrieving messages: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
