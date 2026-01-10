"""
Rate limiting middleware
"""
from fastapi import Request, HTTPException, status
from collections import defaultdict
from datetime import datetime, timedelta
import asyncio

class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)
        self.cleanup_task = None
    
    async def check_rate_limit(self, identifier: str) -> bool:
        """Check if request is within rate limit"""
        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)
        
        # Clean old requests
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if req_time > minute_ago
        ]
        
        # Check limit
        if len(self.requests[identifier]) >= self.requests_per_minute:
            return False
        
        # Add current request
        self.requests[identifier].append(now)
        return True
    
    async def cleanup_old_entries(self):
        """Periodically cleanup old entries"""
        while True:
            await asyncio.sleep(300)  # Every 5 minutes
            now = datetime.utcnow()
            minute_ago = now - timedelta(minutes=1)
            
            # Remove empty entries
            to_remove = []
            for identifier, times in self.requests.items():
                self.requests[identifier] = [t for t in times if t > minute_ago]
                if not self.requests[identifier]:
                    to_remove.append(identifier)
            
            for identifier in to_remove:
                del self.requests[identifier]

# Global rate limiter instance
rate_limiter = RateLimiter(requests_per_minute=60)

async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware"""
    # Skip rate limiting for static files
    if request.url.path.startswith("/static"):
        return await call_next(request)
    
    # Get identifier (IP address or user ID from token)
    identifier = request.client.host
    
    # Check rate limit
    if not await rate_limiter.check_rate_limit(identifier):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later."
        )
    
    return await call_next(request)
