import asyncio
import os
import urllib.request
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.routers import admin, analytics, audit, auth, governance, knowledge
from app.utils.logger import logger


async def _self_ping_loop():
    """Background task to keep Render free tier awake by pinging itself every 12 minutes."""
    public_url = os.getenv("RENDER_EXTERNAL_URL") or "https://brandsentinel-i28k.onrender.com"
    health_url = f"{public_url.rstrip('/')}/health"
    await asyncio.sleep(60)
    while True:
        try:
            def _ping():
                req = urllib.request.Request(health_url, headers={"User-Agent": "BrandSentinel-KeepAlive"})
                with urllib.request.urlopen(req, timeout=15) as resp:
                    return resp.status
            status = await asyncio.to_thread(_ping)
            logger.info(f"Keep-alive self ping to {health_url}: HTTP {status}")
        except Exception as e:
            logger.debug(f"Keep-alive notice: {e}")
        # Sleep for 12 minutes (Render idle timeout is 15 minutes)
        await asyncio.sleep(720)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database tables
    logger.info("Initializing database schemas...")
    init_db()
    logger.info("Database schemas initialized successfully.")

    # Auto-seed initial demo dataset if requested
    if settings.AUTO_SEED or os.getenv("AUTO_SEED", "false").lower() == "true":
        logger.info("AUTO_SEED enabled: populating demo dataset...")
        try:
            from scripts.seed_demo import seed_demo_data
            seed_demo_data()
            logger.info("Demo data seeding completed successfully.")
        except Exception as e:
            logger.error(f"AUTO_SEED notice: {e}")

    # Start keep-alive loop
    ping_task = asyncio.create_task(_self_ping_loop())

    yield
    # Shutdown
    ping_task.cancel()
    logger.info("BrandSentinel backend shutting down.")


app = FastAPI(
    title=settings.APP_NAME,
    description="Intelligent Brand-Governance Platform API with Tri-Engine Verification",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS for Next.js frontend and live production origins
cors_origins_raw = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
default_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
for d in default_origins:
    if d not in cors_origins_raw and "*" not in cors_origins_raw:
        cors_origins_raw.append(d)

allow_all = "*" in cors_origins_raw

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if allow_all else cors_origins_raw,
    allow_origin_regex=r"^https?://.*" if allow_all else None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers under /api/v1
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(knowledge.router, prefix=settings.API_V1_PREFIX)
app.include_router(audit.router, prefix=settings.API_V1_PREFIX)
app.include_router(governance.router, prefix=settings.API_V1_PREFIX)
app.include_router(analytics.router, prefix=settings.API_V1_PREFIX)
app.include_router(admin.router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0",
    }
