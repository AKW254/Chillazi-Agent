import time
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.utils.logger import logger


# --------------------------------------------------
# Logging Middleware
# --------------------------------------------------

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(f"Unhandled error: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"error": "Internal Server Error"}
            )

        process_time = time.time() - start_time

        logger.info(
            f"{request.method} {request.url.path} "
            f"Status: {response.status_code} "
            f"Time: {process_time:.4f}s"
        )

        response.headers["X-Process-Time"] = str(process_time)

        return response


# --------------------------------------------------
# Security Headers Middleware
# --------------------------------------------------

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"

        return response


# --------------------------------------------------
# Simple Rate Limiting Middleware (Basic)
# --------------------------------------------------

RATE_LIMIT = {}
MAX_REQUESTS = 100
WINDOW_SECONDS = 60


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        current_time = time.time()

        if client_ip not in RATE_LIMIT:
            RATE_LIMIT[client_ip] = []

        # Remove old timestamps
        RATE_LIMIT[client_ip] = [
            t for t in RATE_LIMIT[client_ip]
            if current_time - t < WINDOW_SECONDS
        ]

        if len(RATE_LIMIT[client_ip]) >= MAX_REQUESTS:
            return JSONResponse(
                status_code=429,
                content={"error": "Too many requests"}
            )

        RATE_LIMIT[client_ip].append(current_time)

        return await call_next(request)


# --------------------------------------------------
# Middleware Registration Function
# --------------------------------------------------

def register_middleware(app: FastAPI):
    """
    Register all application middleware here.
    Order matters: first added = outermost layer
    """

    app.add_middleware(LoggingMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware)

    logger.info("Middleware registered successfully")