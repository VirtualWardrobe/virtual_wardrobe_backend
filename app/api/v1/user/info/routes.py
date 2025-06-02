from fastapi import APIRouter, HTTPException, Depends, status
from app.db.prisma_client import get_prisma
from app.redis.redis_client import redis_handler
from app.utils.success_handler import success_response
from app.api.v1.user.auth.routes.user import get_current_user
from app.api.v1.user.info.models import UpdateUserInfo
from prisma import Prisma
import logging, json


router = APIRouter()


@router.get("/user", status_code=status.HTTP_200_OK)
async def get_user_info(
    prisma: Prisma = Depends(get_prisma),
    current_user = Depends(get_current_user)
):
    try:
        cache_key = f"user_info_{current_user.id}"
        redis_client = await redis_handler.get_client()
        cached_user = await redis_client.get(cache_key)

        if cached_user:
            return success_response(
                message="User information retrieved from cache",
                data=json.loads(cached_user)
            )
        
        user = await prisma.user.find_first(
            where={"id": current_user.id, "is_deleted": False},
            include={
                "VirtualTryOn": True
            }
        )

        user_dict = user.model_dump(mode='json')
        await redis_client.setex(cache_key, 3600, json.dumps(user_dict))

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
    prisma: Prisma = Depends(get_prisma),
    current_user = Depends(get_current_user)
):
    try:     
        update_data = request.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields provided for update"
            )

        async with prisma.tx(timeout=65000,max_wait=80000) as tx:
            updated_user = await tx.user.update(
                where={"id": current_user.id, "is_deleted": False},
                data=update_data
            )

            cache_key = f"user_info_{current_user.id}"
            redis_client = await redis_handler.get_client()
            await redis_client.delete(cache_key)

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
    prisma: Prisma = Depends(get_prisma),
    current_user = Depends(get_current_user)
):
    try:        
        # soft delete the user
        async with prisma.tx(timeout=65000,max_wait=80000) as tx:
            await tx.user.update(
                where={"id": current_user.id},
                data={"is_deleted":True}
            )

            cache_key = f"user_info_{current_user.id}"
            redis_client = await redis_handler.get_client()
            await redis_client.delete(cache_key)
        
        return success_response(
            message="User deleted successfully"
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
