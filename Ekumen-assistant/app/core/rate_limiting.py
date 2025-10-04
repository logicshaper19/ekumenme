"""
Rate limiting utilities for the application
"""

import os
import logging
from datetime import datetime, timedelta
from collections import defaultdict
from fastapi import HTTPException, status, Request
from app.models.user import User

logger = logging.getLogger(__name__)

def is_development_mode() -> bool:
    """Check if we're running in development mode"""
    return os.getenv("ENVIRONMENT", "production").lower() in ["development", "dev", "local"]

class RateLimiter:
    """Simple in-memory rate limiter (for production, use Redis)"""
    
    def __init__(self):
        self.requests = defaultdict(list)
        self.cleanup_interval = 300  # 5 minutes
        self.last_cleanup = datetime.utcnow()
    
    def is_allowed(
        self, 
        key: str, 
        limit: int, 
        window_seconds: int = 60
    ) -> bool:
        """Check if request is allowed based on rate limit"""
        now = datetime.utcnow()
        
        # Cleanup old entries periodically
        if (now - self.last_cleanup).total_seconds() > self.cleanup_interval:
            self._cleanup_old_entries(now)
            self.last_cleanup = now
        
        # Remove old entries for this key
        cutoff = now - timedelta(seconds=window_seconds)
        self.requests[key] = [
            req_time for req_time in self.requests[key] 
            if req_time > cutoff
        ]
        
        # Check if under limit
        if len(self.requests[key]) >= limit:
            return False
        
        # Add current request
        self.requests[key].append(now)
        return True
    
    def _cleanup_old_entries(self, now: datetime):
        """Clean up old entries to prevent memory leaks"""
        cutoff = now - timedelta(hours=1)
        keys_to_remove = []
        
        for key, requests in self.requests.items():
            self.requests[key] = [req for req in requests if req > cutoff]
            if not self.requests[key]:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.requests[key]

# Global rate limiter instance
rate_limiter = RateLimiter()

def check_rate_limit(
    request: Request,
    user: User,
    limit: int = 10,
    window_seconds: int = 60
) -> None:
    """
    Check rate limit and raise HTTPException if exceeded
    Utility function - not a FastAPI dependency
    """
    client_ip = request.client.host if request.client else "unknown"
    rate_key = f"upload:{client_ip}:{user.id}"
    
    if not rate_limiter.is_allowed(rate_key, limit, window_seconds):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Maximum {limit} requests per {window_seconds} seconds."
        )
