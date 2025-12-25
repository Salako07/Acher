from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from app.config import settings
from app.routes import auth, projects, invites, checkins, analytics
from app.scheduler import start_scheduler


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting application")
    scheduler = start_scheduler()

    yield

    # Shutdown
    logger.info("Shutting down application")
    scheduler.shutdown()


app = FastAPI(
    title="Accountability System",
    description="A real accountability platform for daily commitments",
    version="2.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with /api prefix
app.include_router(auth.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(invites.router, prefix="/api")
app.include_router(checkins.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "Accountability System API"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}
