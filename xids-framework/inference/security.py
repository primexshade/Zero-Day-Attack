"""
Security module for X-IDS API
Includes JWT authentication, rate limiting, input validation
"""

import jwt
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Callable
from functools import wraps
import time
from collections import defaultdict
import re
import logging

logger = logging.getLogger(__name__)

# Configuration
JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRY_HOURS = 24

class JWTAuth:
    """JWT Authentication handler"""
    
    @staticmethod
    def generate_token(user_id: str, role: str = 'analyst', expires_in_hours: int = JWT_EXPIRY_HOURS) -> str:
        """
        Generate JWT token
        
        Args:
            user_id: User identifier
            role: User role (analyst, admin, viewer)
            expires_in_hours: Token expiry time
            
        Returns:
            JWT token string
        """
        payload = {
            'user_id': user_id,
            'role': role,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=expires_in_hours)
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict]:
        """
        Verify JWT token
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded payload or None if invalid
        """
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
    
    @staticmethod
    def require_auth(allowed_roles: list = None):
        """
        Decorator for protecting endpoints
        
        Args:
            allowed_roles: List of allowed roles (default: all)
        """
        def decorator(f: Callable) -> Callable:
            @wraps(f)
            def decorated_function(*args, **kwargs):
                # Get token from headers (if using Flask/FastAPI)
                # This is a template - actual implementation depends on framework
                token = kwargs.get('token') or args[0] if args else None
                
                if not token:
                    logger.error("No token provided")
                    raise PermissionError("Authentication required")
                
                payload = JWTAuth.verify_token(token)
                if not payload:
                    raise PermissionError("Invalid or expired token")
                
                if allowed_roles and payload.get('role') not in allowed_roles:
                    raise PermissionError(f"Role {payload.get('role')} not allowed")
                
                # Add user info to kwargs
                kwargs['current_user'] = payload
                return f(*args, **kwargs)
            
            return decorated_function
        return decorator


class RateLimiter:
    """Rate limiting handler"""
    
    def __init__(self, requests_per_second: int = 100):
        """
        Initialize rate limiter
        
        Args:
            requests_per_second: Max requests per second per client
        """
        self.rps = requests_per_second
        self.clients = defaultdict(list)
    
    def is_allowed(self, client_id: str) -> bool:
        """
        Check if client is within rate limit
        
        Args:
            client_id: Client identifier (IP or user ID)
            
        Returns:
            True if request is allowed, False otherwise
        """
        now = time.time()
        window_start = now - 1.0  # 1 second window
        
        # Clean old requests
        self.clients[client_id] = [
            t for t in self.clients[client_id] if t > window_start
        ]
        
        # Check limit
        if len(self.clients[client_id]) < self.rps:
            self.clients[client_id].append(now)
            return True
        
        return False
    
    def get_remaining(self, client_id: str) -> int:
        """Get remaining requests for client"""
        now = time.time()
        window_start = now - 1.0
        
        requests_in_window = len([
            t for t in self.clients[client_id] if t > window_start
        ])
        return max(0, self.rps - requests_in_window)


class InputValidator:
    """Input validation and sanitization"""
    
    # Regular expressions for validation
    IP_PATTERN = r'^(\d{1,3}\.){3}\d{1,3}$'
    DOMAIN_PATTERN = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
    EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    UUID_PATTERN = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    
    @staticmethod
    def validate_ip(ip: str) -> bool:
        """Validate IP address"""
        if not isinstance(ip, str):
            return False
        if not re.match(InputValidator.IP_PATTERN, ip):
            return False
        parts = ip.split('.')
        return all(0 <= int(part) <= 255 for part in parts)
    
    @staticmethod
    def validate_domain(domain: str) -> bool:
        """Validate domain name"""
        if not isinstance(domain, str) or len(domain) > 253:
            return False
        return bool(re.match(InputValidator.DOMAIN_PATTERN, domain))
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email address"""
        if not isinstance(email, str) or len(email) > 254:
            return False
        return bool(re.match(InputValidator.EMAIL_PATTERN, email))
    
    @staticmethod
    def validate_uuid(uuid_str: str) -> bool:
        """Validate UUID"""
        if not isinstance(uuid_str, str):
            return False
        return bool(re.match(InputValidator.UUID_PATTERN, uuid_str.lower()))
    
    @staticmethod
    def sanitize_string(s: str, max_length: int = 1000) -> str:
        """Sanitize string input"""
        if not isinstance(s, str):
            return ""
        
        # Truncate
        s = s[:max_length]
        
        # Remove potentially dangerous characters
        s = s.replace('<', '&lt;').replace('>', '&gt;')
        s = s.replace('"', '&quot;').replace("'", '&#x27;')
        
        return s
    
    @staticmethod
    def validate_json_features(features: list, max_features: int = 1000) -> bool:
        """Validate feature array"""
        if not isinstance(features, list):
            return False
        if len(features) > max_features:
            return False
        if not all(isinstance(f, (int, float)) for f in features):
            return False
        return True


class SecurityHeaders:
    """HTTP security headers"""
    
    @staticmethod
    def get_secure_headers() -> Dict[str, str]:
        """Get recommended security headers"""
        return {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': "default-src 'self'",
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        }


# Example usage for FastAPI
def example_fastapi_setup():
    """Example of using security features with FastAPI"""
    try:
        from fastapi import FastAPI, Depends, HTTPException, Header
        from fastapi.middleware.cors import CORSMiddleware
        
        app = FastAPI()
        rate_limiter = RateLimiter(requests_per_second=100)
        
        # Add CORS with restrictions
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["https://yourdomain.com"],  # Specify allowed origins
            allow_credentials=True,
            allow_methods=["GET", "POST"],
            allow_headers=["Authorization", "Content-Type"],
        )
        
        # Login endpoint
        @app.post("/auth/login")
        def login(username: str, password: str):
            # TODO: Verify credentials against secure database
            token = JWTAuth.generate_token(username, role='analyst')
            return {"access_token": token, "token_type": "bearer"}
        
        # Protected endpoint example
        @app.post("/api/predict")
        def predict(features: list, authorization: str = Header(None)):
            # Check rate limit
            client_id = "anonymous"  # In real app, extract from JWT
            if not rate_limiter.is_allowed(client_id):
                raise HTTPException(status_code=429, detail="Rate limit exceeded")
            
            # Validate input
            if not InputValidator.validate_json_features(features):
                raise HTTPException(status_code=400, detail="Invalid features")
            
            # Your prediction logic here
            prediction = {"result": 0.85}
            
            return prediction
        
        return app
    
    except ImportError:
        print("FastAPI not installed")
        return None


if __name__ == "__main__":
    # Test JWT
    token = JWTAuth.generate_token("user123", "analyst")
    print(f"Generated token: {token[:50]}...")
    
    payload = JWTAuth.verify_token(token)
    print(f"Verified payload: {payload}")
    
    # Test rate limiter
    limiter = RateLimiter(100)
    for i in range(5):
        allowed = limiter.is_allowed("client1")
        print(f"Request {i+1}: {'allowed' if allowed else 'denied'}")
    
    # Test validators
    print(f"\nIP validation: {InputValidator.validate_ip('192.168.1.1')}")
    print(f"Email validation: {InputValidator.validate_email('user@example.com')}")
    print(f"UUID validation: {InputValidator.validate_uuid('550e8400-e29b-41d4-a716-446655440000')}")
    
    print(f"\nSecurity headers: {SecurityHeaders.get_secure_headers()}")
