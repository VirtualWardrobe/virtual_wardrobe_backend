from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.user.auth.routes.user import router as user_auth_router
from app.api.v1.user.auth.routes.google_auth import router as google_auth_router
from app.api.v1.user.info.routes import router as user_info_router
from app.api.v1.wardrobe_items.routes import router as item_router
from app.api.v1.contacts.routes import router as contact_router
from contextlib import asynccontextmanager
from app.db.prisma_client import PrismaClient

@asynccontextmanager
async def lifespan(app: FastAPI):
    await PrismaClient.get_instance()
    yield
    await PrismaClient.close_connection()

app = FastAPI(
    title="Virtual Wardrobe Backend",
    description="API for managing all operations",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins="http://127.0.0.1:5500",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_auth_router, prefix="/api/v1", tags=["User Auth"])
app.include_router(google_auth_router, prefix="/api/v1", tags=["Google Auth"])
app.include_router(user_info_router, prefix="/api/v1", tags=["User Info"])
app.include_router(item_router, prefix="/api/v1", tags=["Wardrobe Items"])
app.include_router(contact_router, prefix="/api/v1", tags=["Contacts"])

@app.get("/")
async def root():
    return {"message": "Welcome to the API"}
