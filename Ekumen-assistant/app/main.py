"""
Agricultural Chatbot FastAPI Application
Main entry point for the agricultural AI assistant
"""

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import time
import logging
import uuid
import json
import asyncio
from datetime import datetime

# Rate limiting imports (optional - only if slowapi is installed)
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    RATE_LIMITING_AVAILABLE = True
except ImportError:
    RATE_LIMITING_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("slowapi not installed - rate limiting disabled")

from app.core.config import settings
from app.core.database import init_db, close_db
from app.api.v1 import auth, chat, journal, products, chat_optimized, feedback, admin, knowledge_base, knowledge_base_workflow

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Initialize rate limiter if available
if RATE_LIMITING_AVAILABLE:
    limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "X-Process-Time"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.localhost"]
)

# Add request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Include API routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(chat_optimized.router, prefix="/api/v1/chat", tags=["chat-optimized"])
app.include_router(journal.router, prefix="/api/v1/journal", tags=["journal"])
app.include_router(products.router, prefix="/api/v1/products", tags=["products"])
app.include_router(feedback.router, prefix="/api/v1/feedback", tags=["feedback"])
app.include_router(admin.router, prefix="/api/v1", tags=["super-admin"])
app.include_router(knowledge_base.router, prefix="/api/v1", tags=["knowledge-base"])
app.include_router(knowledge_base_workflow.router, prefix="/api/v1/knowledge-base", tags=["knowledge-base-workflow"])

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "timestamp": time.time()
    }



# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "version": settings.VERSION,
        "description": settings.DESCRIPTION,
        "docs_url": "/docs" if settings.DEBUG else "Documentation not available in production",
        "api_url": "/api/v1"
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    await init_db()
    logger.info("Database initialized successfully")
    
    # Start knowledge base scheduler
    try:
        from app.services.scheduler_service import start_knowledge_base_scheduler
        start_knowledge_base_scheduler()
        logger.info("Knowledge base scheduler started")
    except Exception as e:
        logger.error(f"Failed to start knowledge base scheduler: {e}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down application")
    
    # Stop knowledge base scheduler
    try:
        from app.services.scheduler_service import stop_knowledge_base_scheduler
        stop_knowledge_base_scheduler()
        logger.info("Knowledge base scheduler stopped")
    except Exception as e:
        logger.error(f"Failed to stop knowledge base scheduler: {e}")
    
    await close_db()
    logger.info("Database connections closed")

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler with comprehensive logging"""
    # Generate request ID for tracking
    request_id = str(uuid.uuid4())[:8]

    # Log comprehensive error details
    logger.error(
        f"Global exception [ID: {request_id}]: {exc}",
        extra={
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "client_ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown"),
            "exception_type": type(exc).__name__,
        },
        exc_info=True
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please contact support with this ID.",
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
