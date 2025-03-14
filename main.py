from fastapi import FastAPI
from app.contacts.routes import router as contact_router
from app.items.routes import router as item_router
from app.users.routes import router as user_router
from contextlib import asynccontextmanager
from app.prisma_client import PrismaClient

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await PrismaClient.close_connection()

app = FastAPI(
    title="Virtual Wardrobe Backend",
    description="API for managing all operations",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(user_router, prefix="/api", tags=["Users"])
app.include_router(item_router, prefix="/api", tags=["Items"])
app.include_router(contact_router, prefix="/api", tags=["Contacts"])

@app.get("/")
async def root():
    return {"message": "Welcome to the API"}
