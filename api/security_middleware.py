"""
FastAPI middleware and security utilities.
Provides rate limiting, CORS, and security headers.
"""
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from datetime import datetime
import time

from django.conf import settings

logger = logging.getLogger("auth")
security_logger = logging.getLogger("security")


_DOCS_PATHS = {"/docs", "/redoc", "/openapi.json"}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        if settings.DEBUG and (
            request.url.path.startswith("/docs")
            or request.url.path.startswith("/redoc")
            or request.url.path.startswith("/openapi.json")
        ):
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "img-src 'self' data: https://fastapi.tiangolo.com;"
            )
        else:
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'"
            )

        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )

        # Swagger UI/ReDoc load their JS/CSS from a CDN and run an inline
        # init script — "default-src 'self'" blocks both, which is why the
        # docs page rendered blank. Relax CSP only for the docs routes
        # themselves; every real API response keeps the strict policy.
        if request.url.path in _DOCS_PATHS:
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' cdn.jsdelivr.net; "
                "img-src 'self' data: fastapi.tiangolo.com cdn.jsdelivr.net; "
                "connect-src 'self'"
            )
        else:
            response.headers["Content-Security-Policy"] = "default-src 'self'"

        return response
        # response.headers["Content-Security-Policy"] = "default-src 'self'"
        # response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        # return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests for auditing"""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Extract request info
        method = request.method
        path = request.url.path
        client_host = request.client.host if request.client else "unknown"

        # Get response
        response = await call_next(request)

        # Log
        duration = time.time() - start_time
        logger.info(
            f"{method} {path} - {response.status_code} - {duration:.3f}s - {client_host}"
        )

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple rate limiting middleware.
    For production, use Redis-based rate limiting instead.
    """

    def __init__(self, app, requests_per_minute: int = 100):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests = {}  # Simple in-memory store (not suitable for distributed systems)

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        now = datetime.now().timestamp()
        current_minute = int(now / 60)

        # Initialize bucket for this minute
        key = f"{client_ip}:{current_minute}"
        if key not in self.requests:
            self.requests[key] = 0
            # Cleanup old buckets
            cutoff = current_minute - 5
            for k in list(self.requests.keys()):
                if int(k.split(":")[1]) < cutoff:
                    del self.requests[k]

        # Check rate limit
        if self.requests[key] >= self.requests_per_minute:
            security_logger.warning(f"Rate limit exceeded for {client_ip}")
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests"},
            )

        self.requests[key] += 1
        response = await call_next(request)
        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Handle exceptions and return proper error responses"""

    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            security_logger.error(f"Unhandled exception: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"},
            )


def setup_security_middleware(app: FastAPI) -> None:
    """
    Setup all security middleware for FastAPI application.
    
    Args:
        app: FastAPI application instance
    """

    # Security headers
    app.add_middleware(SecurityHeadersMiddleware)

    # Request logging
    app.add_middleware(RequestLoggingMiddleware)

    # Rate limiting (consider Redis in production)
    app.add_middleware(RateLimitMiddleware, requests_per_minute=1000)

    # Error handling
    app.add_middleware(ErrorHandlingMiddleware)

    # CORS - must be last. Deny-by-default if the setting is ever missing —
    # a wildcard fallback here combined with allow_credentials=True below
    # would be the classic wildcard+credentials CORS misconfiguration.
    cors_origins = settings.CORS_ALLOWED_ORIGINS if hasattr(settings, 'CORS_ALLOWED_ORIGINS') else []
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Total-Count", "X-Page-Number"],
    )

    logger.info("Security middleware setup completed")


def get_client_ip(request: Request) -> str:
    """Extract client IP from request"""
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
