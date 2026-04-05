"""Security middleware for X-IDS API"""

import logging
from datetime import datetime, timedelta
from typing import Optional
import jwt
from functools import wraps

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# JWT Configuration
JWT_SECRET = "xids-secret-key-change-in-production"
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24

# Rate limiting storage (in production, use Redis)
rate_limit_store = {}


class JWTAuth:
    """JWT authentication helper"""
    
    @staticmethod
    def create_token(user_id: str, roles: list = None) -> str:
        """Create JWT token"""
        if roles is None:
            roles = ["user"]
        
        payload = {
            "user_id": user_id,
            "roles": roles,
            "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS),
            "iat": datetime.utcnow()
        }
        
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        return token
    
    @staticmethod
    def verify_token(token: str) -> dict:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )


class RateLimiter:
    """Rate limiting helper"""
    
    def __init__(self, requests_per_minute: int = 100):
        self.requests_per_minute = requests_per_minute
        self.window_seconds = 60
    
    def is_allowed(self, client_id: str) -> bool:
        """Check if client is within rate limit"""
        now = datetime.utcnow()
        
        if client_id not in rate_limit_store:
            rate_limit_store[client_id] = []
        
        # Remove old requests outside the window
        rate_limit_store[client_id] = [
            req_time for req_time in rate_limit_store[client_id]
            if (now - req_time).total_seconds() < self.window_seconds
        ]
        
        # Check limit
        if len(rate_limit_store[client_id]) >= self.requests_per_minute:
            return False
        
        # Add current request
        rate_limit_store[client_id].append(now)
        return True


class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware for request validation"""
    
    async def dispatch(self, request: Request, call_next):
        # Add security headers
        response = await call_next(request)
        
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response


class InputValidator:
    """Input validation helper"""
    
    @staticmethod
    def validate_features(features: list, expected_count: int = 77) -> bool:
        """Validate input features"""
        if not isinstance(features, list):
            raise HTTPException(status_code=400, detail="Features must be a list")
        
        if len(features) != expected_count:
            raise HTTPException(
                status_code=400,
                detail=f"Expected {expected_count} features, got {len(features)}"
            )
        
        if not all(isinstance(f, (int, float)) for f in features):
            raise HTTPException(status_code=400, detail="All features must be numeric")
        
        return True
