from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Config & Core
from app.config.settings import settings
from app.config.database import init_db

# Middleware
from app.core.middleware import register_middleware

# Routes (import modules directly to avoid package __init__ issues)
import app.api.routes.menu as menu
import app.api.routes.chat as chat
import app.api.routes.order as orders
import app.api.routes.users as users
import app.api.routes.cart as cart
import app.api.routes.roles as roles

# Logger (optional but recommended)
from app.utils.logger import logger


# --------------------------------------------------
# App Initialization
# --------------------------------------------------

def create_app() -> FastAPI:
    app = FastAPI(
        title="Food Ordering AI Chatbot",
        version="1.0.0",
        description="LangChain-powered food ordering assistant"
    )

    # --------------------------------------------------
    # CORS
    # --------------------------------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.get_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --------------------------------------------------
    # Custom Middleware
    # --------------------------------------------------
    register_middleware(app)

    # --------------------------------------------------
    # Routes
    # --------------------------------------------------
    # include routers from individual modules
    app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
    app.include_router(orders.router, prefix="/api/orders", tags=["Orders"])
    app.include_router(menu.router, prefix="/api/menu", tags=["Menu"])
    app.include_router(users.router, prefix="/api/users", tags=["Users"])
    app.include_router(cart.router, prefix="/api/carts", tags=["Carts"])
    app.include_router(roles.router, prefix="/api/roles", tags=["Roles"])

    # --------------------------------------------------
    # Startup Event
    # --------------------------------------------------
    @app.on_event("startup")
    async def startup_event():
        logger.info("Starting Food Ordering Chatbot API...")
        init_db()

    # --------------------------------------------------
    # Shutdown Event
    # --------------------------------------------------
    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Shutting down API...")

    # --------------------------------------------------
    # Health Check
    # --------------------------------------------------
    @app.get("/health", tags=["Health"])
    def health_check():
        return {"status": "ok"}

    return app


# --------------------------------------------------
# App Instance
# --------------------------------------------------

app = create_app()
