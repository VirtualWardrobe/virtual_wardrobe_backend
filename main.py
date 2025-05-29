import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.db.prisma_client import PrismaClient
from app.api.v1.user.auth.routes.user import router as user_auth_router
from app.api.v1.user.auth.routes.google_auth import router as google_auth_router
from app.api.v1.user.info.routes import router as user_info_router
from app.api.v1.wardrobe_items.routes import router as item_router
from app.api.v1.contacts.routes import router as contact_router
from app.api.v1.virtual_tryon.routes import router as virtual_tryon_router

LOG_PATH = "/var/log/fastapi/app.log"
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

file_handler = logging.FileHandler(LOG_PATH)
file_handler.setFormatter(logging.Formatter(LOG_FORMAT))

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter(LOG_FORMAT))

logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, stream_handler]
)

for logger_name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
    uvicorn_logger = logging.getLogger(logger_name)
    uvicorn_logger.handlers = [file_handler, stream_handler]
    uvicorn_logger.setLevel(logging.INFO)
    uvicorn_logger.propagate = False

logger = logging.getLogger(__name__)
logger.info("Logging is set up correctly.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Prisma client")
    await PrismaClient.get_instance()
    yield
    logger.info("Shutting down Prisma client")
    await PrismaClient.close_connection()

app = FastAPI(
    title="Virtual Wardrobe Backend",
    description="API for managing all operations",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_auth_router, prefix="/api/v1", tags=["User Auth"])
app.include_router(google_auth_router, prefix="/api/v1", tags=["Google Auth"])
app.include_router(user_info_router, prefix="/api/v1", tags=["User Info"])
app.include_router(item_router, prefix="/api/v1", tags=["Wardrobe Items"])
app.include_router(contact_router, prefix="/api/v1", tags=["Contacts"])
app.include_router(virtual_tryon_router, prefix="/api/v1", tags=["Virtual Try-On"])

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "Welcome to the API"}
