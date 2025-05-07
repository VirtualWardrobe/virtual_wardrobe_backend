from fastapi import APIRouter, HTTPException, Depends, status
from passlib.context import CryptContext
from app.db.prisma_client import get_prisma
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict
from jose import jwt, JWTError, ExpiredSignatureError
from app.api.v1.user.auth.models.user import Register, OTPVerify, Login, ResetPassword
from app.api.v1.user.auth.mails.templates import sign_up_template, forgot_password_template
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.utils.mail_handler import send_mail
from app.utils.success_handler import success_response
from prisma import Prisma
from prisma.enums import Role
from env import env
import logging, random


# Configuration constants
SECRET_KEY = env.JWT_SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440 # 24 hours

# OAuth2 scheme for token extraction from requests
bearer_scheme = HTTPBearer()

def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token
    
    Args:
        data: Dictionary containing claims to encode in the token
        expires_delta: Optional expiration time delta
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    # Set expiration time
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    # Create encoded JWT
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)


router = APIRouter()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    prisma: Prisma = Depends(get_prisma)
):
    try:
        token = credentials.credentials
        try:
            # Decode and verify token including expiration
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
            
        email = payload.get("email")
        user_id = payload.get("id")
        
        if email is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token claims"
            )
        
        user = await prisma.user.find_first(where={"email": email, "id": user_id, "is_deleted": False})

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="User not found"
            )

        return user
    
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


async def get_current_admin(current_user=Depends(get_current_user)):
    if current_user.role != Role.ADMIN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin access only !")
    
    return current_user


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    request: Register,
    prisma: Prisma =  Depends(get_prisma)
):
    try:        
        async with prisma.tx(timeout=65000,max_wait=80000) as tx:

            existing_user=await tx.user.find_first(where={"email":request.email, "is_deleted":False})
            if existing_user:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already registered with given email")

            #TODO verify the emails if belong to valid domain

            otp = str(random.randint(100000,999999))
            session = await tx.otpsession.find_first(where={"email":request.email, "type":"signup"})
            if session:
                await tx.otpsession.delete_many(where={"session_id":session.session_id})

            session = await tx.otpsession.create(data={
                "name":request.name,
                "email":request.email,
                "hashed_password":get_password_hash(request.password),
                "otp":otp
            })

            await send_mail(
                contacts=[request.email],
                subject="Virtual Wardrobe: Verify Your Account",
                message=sign_up_template(otp)  
            )

            return success_response(message="OTP Sent to your respective email !", data={
                "session_id":session.session_id
            })
   
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


@router.put("/verify/otp", status_code=status.HTTP_200_OK)
async def verify_otp(
    request: OTPVerify,
    prisma: Prisma = Depends(get_prisma)
):
    try:
        async with prisma.tx(timeout=65000,max_wait=80000) as tx:   

            session = await tx.otpsession.find_first(where={"session_id":request.session_id})

            if not session:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Session doesn't exist !")
            
            if session.otp != request.otp:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP is incorrect !")

            user = await tx.user.create(
                data={
                    "name" : session.name,
                    "email": session.email,
                    "hashed_password": session.hashed_password,
                    "is_email_verified": True
                }
            )

            await tx.otpsession.delete_many(where={"session_id":session.session_id})

            return success_response(message="OTP verified successfully ! Login to the platform")
        
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
    

@router.post("/login", status_code=status.HTTP_200_OK)
async def login(
    request: Login,
    prisma: Prisma = Depends(get_prisma)
):
    try:        
        user = await prisma.user.find_first(where={"email":request.email, "is_deleted":False})
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not registered ! Please register to the platform")
        
        if not verify_password(request.password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password is incorrect !")
        
        access_token = create_access_token(data={
            "id":user.id,
            "email":user.email
        })

        return success_response(message="Login success !", data={
            "access_token": access_token
        })
        
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


@router.post("/refresh-token", status_code=status.HTTP_200_OK)
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    prisma: Prisma = Depends(get_prisma)
):
    try:
        token = credentials.credentials
        
        # Decode the token without verifying expiration
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": False})
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token format"
            )
            
        email = payload.get("email")
        user_id = payload.get("id")
        
        if not email or not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token claims"
            )
            
        # Verify user still exists and is active
        user = await prisma.user.find_first(
            where={"email": email, "id": user_id, "is_deleted": False}
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User no longer exists or is inactive"
            )
            
        # Generate new token
        new_token = create_access_token(
            data={"id": user.id, "email": user.email}
        )
        
        return success_response(
            message="Token refreshed successfully",
            data={"access_token": new_token}
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


@router.post("/forgot-password/{email}", status_code=status.HTTP_200_OK)
async def forgot_password(
    email: str,
    prisma: Prisma = Depends(get_prisma)
):
    try:
        async with prisma.tx(timeout=65000,max_wait=80000) as tx:
            user = await tx.user.find_first(where={"email": email})
            if not user:
                raise HTTPException(404, "User not found")

            otp = str(random.randint(100000,999999))
            
            session = await tx.otpsession.find_first(where={"email":email, "type": "password_reset"})
            if session:
                await tx.otpsession.delete_many(where={"email": email, "type": "password_reset"})

            session = await tx.otpsession.create(data={
                "email": email,
                "otp": otp,
                "type": "password_reset",
                "hashed_password": user.hashed_password
            })
            
            await send_mail(
                contacts=[email],
                subject="Virtual Wardrobe: Password Reset",
                message=forgot_password_template(otp)
            )
            
            return success_response(message="OTP sent to email", data={"session_id": session.session_id})

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
    

@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    request: ResetPassword,
    prisma: Prisma = Depends(get_prisma)
):
    try:       
       async with prisma.tx(timeout=65000,max_wait=80000) as tx:
            session = await tx.otpsession.find_first(where={"email": request.email})
            if not session or session.otp != request.otp:
                raise HTTPException(400, "Invalid OTP")

            await tx.user.update(
                where={"email": request.email}, 
                data={"hashed_password": get_password_hash(request.new_password)}
            )

            await tx.otpsession.delete_many(where={"email": request.email, "type" : "password_reset"})
            
            return success_response(message="Password reset successful")

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
