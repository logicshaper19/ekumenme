"""
Database configuration and connection management
for the agricultural chatbot system
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from typing import AsyncGenerator
import logging
import os

from .config import settings


class DatabaseError(Exception):
    """Custom database error for better error handling"""
    pass

logger = logging.getLogger(__name__)

# Database pool configuration
pool_size = int(os.getenv("DB_POOL_SIZE", "20"))
max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "40"))

# Create async engine for PostgreSQL with PostGIS support
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=pool_size,
    max_overflow=max_overflow,
    pool_timeout=30,  # Add timeout
    pool_reset_on_return='commit'  # Reset connections
)

# Create sync engine for migrations and admin tasks
sync_engine = create_engine(
    settings.DATABASE_URL_SYNC,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=5,
    max_overflow=10,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=True,
    autocommit=False,
)

# Create sync session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine,
)

# Create declarative base
Base = declarative_base()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get async database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            error_context = {
                "session_id": id(session),
                "transaction_active": session.in_transaction(),
                "error_type": type(e).__name__,
                "error_message": str(e)
            }
            logger.error(f"Database session error: {error_context}", exc_info=True)

            try:
                await session.rollback()
                logger.info(f"Session {id(session)} rolled back successfully")
            except Exception as rollback_error:
                logger.error(f"Rollback failed for session {id(session)}: {rollback_error}")

            raise DatabaseError(f"Database operation failed: {str(e)}") from e
        finally:
            await session.close()


def get_sync_db():
    """
    Dependency to get sync database session
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        error_context = {
            "session_id": id(db),
            "error_type": type(e).__name__,
            "error_message": str(e)
        }
        logger.error(f"Sync database session error: {error_context}", exc_info=True)

        try:
            db.rollback()
            logger.info(f"Sync session {id(db)} rolled back successfully")
        except Exception as rollback_error:
            logger.error(f"Sync rollback failed for session {id(db)}: {rollback_error}")

        raise DatabaseError(f"Sync database operation failed: {str(e)}") from e
    finally:
        db.close()


async def init_db():
    """
    Initialize database tables
    """
    try:
        async with async_engine.begin() as conn:
            # Import all models to ensure they are registered
            from app.models import user, conversation, intervention, organization, product

            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        raise


async def close_db():
    """
    Close database connections
    """
    try:
        await async_engine.dispose()
        sync_engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Database close error: {e}")
        raise
