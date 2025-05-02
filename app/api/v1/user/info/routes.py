from fastapi import APIRouter, HTTPException, Depends, status
from app.db.prisma_client import PrismaClient
from app.utils.success_handler import success_response
from app.api.v1.user.auth.routes.user import get_current_user
from app.api.v1.user.info.models import UpdateUserInfo
from prisma import Prisma
import logging


router = APIRouter()


@router.get("/user", status_code=status.HTTP_200_OK)
async def get_user_info(
    prisma: Prisma = Depends(PrismaClient.get_instance),
    current_user = Depends(get_current_user)
):
    try:        
        user = await prisma.user.find_first(
            where={"id": current_user.id, "is_deleted": False}
        )

        return success_response(
            message="User information retrieved successfully",
            data=user
        )
    
    except HTTPException as he:
        logging.error(he)
        raise he
    
    except Exception as e:
        error_code = getattr(e, 'code', 500)
        error_code = getattr(e, 'status_code', error_code)
        
        logging.error(f"Error Code: {error_code}, Message: {str(e)}", exc_info=True)
        
        raise HTTPException(
            status_code=error_code,
            detail=str(e)
        )


@router.patch("/user", status_code=status.HTTP_200_OK)
async def update_user(
    request : UpdateUserInfo,
    prisma: Prisma = Depends(PrismaClient.get_instance),
    current_user = Depends(get_current_user)
):
    try:        
        update_data = request.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields provided for update"
            )

        updated_user = await prisma.user.update(
            where={"id": current_user.id, "is_deleted": False},
            data=update_data
        )

        return success_response(
            message="User updated successfully",
            data=updated_user
        )

    except HTTPException as he:
        logging.error(he)
        raise he
    
    except Exception as e:
        error_code = getattr(e, 'code', 500)
        error_code = getattr(e, 'status_code', error_code)
        
        logging.error(f"Error Code: {error_code}, Message: {str(e)}", exc_info=True)
        
        raise HTTPException(
            status_code=error_code,
            detail=str(e)
        )


@router.delete("/user", status_code=status.HTTP_200_OK)
async def delete_user(
    prisma: Prisma = Depends(PrismaClient.get_instance),
    current_user = Depends(get_current_user)
):
    try:        
        # soft delete the user
        await prisma.user.update(
            where={"id": current_user.id},
            data={"is_deleted":True}
        )
        
        return success_response(message="User deleted successfully")
        
    except HTTPException as he:
        logging.error(he)
        raise he
    
    except Exception as e:
        error_code = getattr(e, 'code', 500)
        error_code = getattr(e, 'status_code', error_code)
        
        logging.error(f"Error Code: {error_code}, Message: {str(e)}", exc_info=True)
        
        raise HTTPException(
            status_code=error_code,
            detail=str(e)
        )

@router.get("/search", status_code=status.HTTP_200_OK)
async def search_users(
    email: str,
    prisma: Prisma = Depends(PrismaClient.get_instance),
):
    try:        
        users = await prisma.user.find_many(
            where={
                "email": {
                    "contains": email,
                    "mode": "insensitive"
                }
            },
            take=5
        )

        formatted_users = []
        for user in users:
            formatted_users.append({"email":user.email, "name":user.name})

        return success_response(
            message="Users retrieved successfully",
            data={"users": formatted_users}
        )
    
    except HTTPException as he:
        logging.error(he)
        raise he
    
    except Exception as e:
        error_code = getattr(e, 'code', 500)
        error_code = getattr(e, 'status_code', error_code)
        
        logging.error(f"Error Code: {error_code}, Message: {str(e)}", exc_info=True)
        
        raise HTTPException(
            status_code=error_code,
            detail=str(e)
        )
