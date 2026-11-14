from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.routers import audit, auth, knowledge
from app.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database tables
    logger.info("Initializing database schemas...")
    init_db()
    logger.info("Database schemas initialized successfully.")
    yield
    # Shutdown
    logger.info("BrandSentinel backend shutting down.")


app = FastAPI(
    title=settings.APP_NAME,
    description="Intelligent Brand-Governance Platform API with Tri-Engine Verification",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers under /api/v1
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(knowledge.router, prefix=settings.API_V1_PREFIX)
app.include_router(audit.router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0",
    }
