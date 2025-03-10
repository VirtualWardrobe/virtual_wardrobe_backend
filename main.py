from fastapi import FastAPI
from app.routes import router as api_router
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

app.include_router(api_router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Welcome to the API"}
