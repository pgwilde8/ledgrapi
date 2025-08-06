"""
LedgrAPI Custom Middleware
Request logging, rate limiting, and security headers
"""

import time
import logging
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging all requests with timing and metadata"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Log request start
        logger.info(
            f"REQUEST_START {request.method} {request.url.path} "
            f"client={request.client.host if request.client else 'unknown'} "
            f"user_agent={request.headers.get('user-agent', 'unknown')}"
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log request completion
            logger.info(
                f"REQUEST_END {request.method} {request.url.path} "
                f"status_code={response.status_code} "
                f"process_time={process_time:.4f}s"
            )
            
            # Add timing header
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # Log error
            process_time = time.time() - start_time
            logger.error(
                f"REQUEST_ERROR {request.method} {request.url.path} "
                f"error={str(e)} process_time={process_time:.4f}s"
            )
            raise

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware for adding security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://cdn.jsdelivr.net; "
            "connect-src 'self' https://api.ledgrapi.com; "
            "frame-ancestors 'none';"
        )
        response.headers["Content-Security-Policy"] = csp
        
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting middleware"""
    
    def __init__(self, app, calls_per_minute: int = 60):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute
        self.requests = {}  # In production, use Redis
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        # Clean old requests (older than 1 minute)
        if client_ip in self.requests:
            self.requests[client_ip] = [
                req_time for req_time in self.requests[client_ip]
                if current_time - req_time < 60
            ]
        
        # Check rate limit
        if client_ip in self.requests and len(self.requests[client_ip]) >= self.calls_per_minute:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Maximum {self.calls_per_minute} requests per minute allowed"
                }
            )
        
        # Add current request
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        self.requests[client_ip].append(current_time)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = self.calls_per_minute - len(self.requests[client_ip])
        response.headers["X-RateLimit-Limit"] = str(self.calls_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        response.headers["X-RateLimit-Reset"] = str(int(current_time + 60))
        
        return response

class APIAuthMiddleware(BaseHTTPMiddleware):
    """Middleware for API key authentication"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip auth for certain endpoints
        if request.url.path in ["/", "/health", "/api/docs", "/api/redoc", "/api/openapi.json"]:
            return await call_next(request)
        
        # Check for API key in headers
        api_key = request.headers.get("X-API-Key") or request.headers.get("Authorization")
        
        if not api_key:
            # Allow public endpoints to pass through
            if request.url.path.startswith("/api/v1/public"):
                return await call_next(request)
            
            logger.warning(f"Missing API key for request: {request.method} {request.url.path}")
            return JSONResponse(
                status_code=401,
                content={
                    "error": "Authentication required",
                    "message": "API key is required for this endpoint"
                }
            )
        
        # TODO: Validate API key against database
        # For now, just log the key
        logger.info(f"API key used: {api_key[:8]}... for {request.method} {request.url.path}")
        
        return await call_next(request) 