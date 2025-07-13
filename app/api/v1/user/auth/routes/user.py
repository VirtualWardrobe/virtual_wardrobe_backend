from fastapi import APIRouter, HTTPException, Depends, status
from passlib.context import CryptContext
from app.db.prisma_client import get_prisma
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict
from jose import jwt, JWTError, ExpiredSignatureError
from app.api.v1.user.auth.models.user import Register, OTPVerify, Login, ResetPassword, EmailOnlyRequest
from app.api.v1.user.auth.mails.templates import sign_up_template, forgot_password_template
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.utils.mail_handler import send_mail
from app.utils.success_handler import success_response
from prisma import Prisma
from prisma.enums import Role
from env import env
import logging, random

SECRET_KEY = env.JWT_SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440

bearer_scheme = HTTPBearer()

def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

router = APIRouter()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    prisma: Prisma = Depends(get_prisma)
):
    try:
        token = credentials.credentials
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        email = payload.get("email")
        user_id = payload.get("id")

        if not email or not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token claims")

        user = await prisma.user.find_first(where={"email": email, "id": user_id, "is_deleted": False})
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

        return user

    except HTTPException as he:
        logging.error("HTTPException: %s", he)
        raise he
    except Exception as e:
        error_code = getattr(e, 'code', getattr(e, 'status_code', 500))
        logging.error("Error Code: %s, Message: %s", error_code, str(e), exc_info=True)
        raise HTTPException(status_code=error_code, detail=str(e))

async def get_current_admin(current_user=Depends(get_current_user)):
    if current_user.role != Role.ADMIN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin access only !")
    return current_user

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(request: Register, prisma: Prisma = Depends(get_prisma)):
    try:
        async with prisma.tx(timeout=65000, max_wait=80000) as tx:
            existing_user = await tx.user.find_first(where={"email": request.email})
            if existing_user:
                if not existing_user.is_deleted:
                    raise HTTPException(status_code=400, detail="User already registered with given email")
                raise HTTPException(status_code=409, detail="An account with this email was deleted. Do you want to restore it?")

            session = await tx.otpsession.find_first(where={"email": request.email, "type": "signup"})
            if session:
                await tx.otpsession.delete_many(where={"session_id": session.session_id})

            otp = str(random.randint(100000, 999999))
            session = await tx.otpsession.create(data={
                "name": request.name,
                "email": request.email,
                "hashed_password": get_password_hash(request.password),
                "otp": otp,
                "type": "signup"
            })

            await send_mail(
                contacts=[request.email],
                subject="Virtual Wardrobe: Verify Your Account",
                message=sign_up_template(otp)
            )

            return success_response(message="OTP sent to your email!", data={"session_id": session.session_id})

    except HTTPException as he:
        logging.error("HTTPException: %s", he)
        raise he
    except Exception as e:
        error_code = getattr(e, 'code', getattr(e, 'status_code', 500))
        logging.error("Error Code: %s, Message: %s", error_code, str(e), exc_info=True)
        raise HTTPException(status_code=error_code, detail=str(e))

@router.put("/verify/otp", status_code=status.HTTP_200_OK)
async def verify_otp(request: OTPVerify, prisma: Prisma = Depends(get_prisma)):
    try:
        async with prisma.tx(timeout=65000, max_wait=80000) as tx:
            session = await tx.otpsession.find_first(where={"session_id": request.session_id})
            if not session:
                raise HTTPException(400, "Session doesn't exist!")
            if session.otp != request.otp:
                raise HTTPException(400, "OTP is incorrect!")

            existing_user = await tx.user.find_first(where={"email": session.email})
            if existing_user:
                if existing_user.is_deleted:
                    raise HTTPException(409, "An account with this email was previously deleted. Please restore it before verifying OTP.")
                raise HTTPException(400, "User already verified. Please login.")

            await tx.user.create(data={
                "name": session.name,
                "email": session.email,
                "hashed_password": session.hashed_password,
                "is_email_verified": True
            })

            await tx.otpsession.delete_many(where={"session_id": session.session_id})
            return success_response(message="OTP verified successfully! Login to the platform")

    except HTTPException as he:
        logging.error("HTTPException: %s", he)
        raise he
    except Exception as e:
        error_code = getattr(e, 'code', getattr(e, 'status_code', 500))
        logging.error("Error Code: %s, Message: %s", error_code, str(e), exc_info=True)
        raise HTTPException(status_code=error_code, detail=str(e))

@router.post("/resend-otp", status_code=status.HTTP_200_OK)
async def resend_otp(session_id: str, prisma: Prisma = Depends(get_prisma)):
    try:
        async with prisma.tx(timeout=65000, max_wait=80000) as tx:
            session = await tx.otpsession.find_first(where={"session_id": session_id})
            if not session:
                raise HTTPException(400, "Session doesn't exist!")

            otp = str(random.randint(100000, 999999))
            await tx.otpsession.update(where={"session_id": session.session_id}, data={"otp": otp})

            await send_mail(
                contacts=[session.email],
                subject="Virtual Wardrobe: Verify Your Account",
                message=sign_up_template(otp)
            )

            return success_response(message="OTP resent successfully!", data={"session_id": session.session_id})

    except HTTPException as he:
        logging.error("HTTPException: %s", he)
        raise he
    except Exception as e:
        error_code = getattr(e, 'code', getattr(e, 'status_code', 500))
        logging.error("Error Code: %s, Message: %s", error_code, str(e), exc_info=True)
        raise HTTPException(status_code=error_code, detail=str(e))

@router.post("/login", status_code=status.HTTP_200_OK)
async def login(request: Login, prisma: Prisma = Depends(get_prisma)):
    try:
        user = await prisma.user.find_first(where={"email": request.email})
        if not user:
            raise HTTPException(404, "User not registered! Please register to the platform.")
        if not verify_password(request.password, user.hashed_password):
            raise HTTPException(400, "Password is incorrect!")
        if user.is_deleted:
            raise HTTPException(409, "This account is soft-deleted. Would you like to restore it?")

        access_token = create_access_token(data={"id": user.id, "email": user.email})
        return success_response(message="Login success!", data={"access_token": access_token})

    except HTTPException as he:
        logging.error("HTTPException: %s", he)
        raise he
    except Exception as e:
        error_code = getattr(e, 'code', getattr(e, 'status_code', 500))
        logging.error("Error Code: %s, Message: %s", error_code, str(e), exc_info=True)
        raise HTTPException(status_code=error_code, detail=str(e))

# ... (Continue applying same logging style to the remaining endpoints such as refresh-token, forgot-password, reset-password, restore-account, etc.)
