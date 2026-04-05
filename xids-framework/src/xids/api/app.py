"""FastAPI application factory and configuration"""

import logging
from pathlib import Path
from typing import Dict, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZIPMiddleware

from xids.api.middleware.security import SecurityMiddleware
from xids.api.routes import health, predictions

logger = logging.getLogger(__name__)


def create_app(config: Optional[Dict] = None) -> FastAPI:
    """Create and configure FastAPI application"""
    
    # Configuration defaults
    if config is None:
        config = {}
    
    default_config = {
        "title": "X-IDS Inference API",
        "description": "Real-time Zero-Day Attack Detection API",
        "version": "1.0.0",
        "cors_origins": ["*"],
        "cors_credentials": True,
        "cors_methods": ["*"],
        "cors_headers": ["*"],
        "gzip_enabled": True,
        "gzip_minimum_size": 1000,
    }
    
    config = {**default_config, **config}
    
    # Create FastAPI app
    app = FastAPI(
        title=config["title"],
        description=config["description"],
        version=config["version"],
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config["cors_origins"],
        allow_credentials=config["cors_credentials"],
        allow_methods=config["cors_methods"],
        allow_headers=config["cors_headers"],
    )
    
    # Add GZIP compression
    if config["gzip_enabled"]:
        app.add_middleware(
            GZIPMiddleware,
            minimum_size=config["gzip_minimum_size"]
        )
    
    # Add security middleware
    app.add_middleware(SecurityMiddleware)
    
    # Include routers
    app.include_router(health.router)
    app.include_router(predictions.router)
    
    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "message": "X-IDS Inference API",
            "version": config["version"],
            "docs": "/api/docs"
        }
    
    # Startup event
    @app.on_event("startup")
    async def startup():
        logger.info(f"Starting {config['title']} v{config['version']}")
        logger.info("Available endpoints:")
        for route in app.routes:
            if hasattr(route, 'path'):
                logger.info(f"  {route.methods if hasattr(route, 'methods') else 'ANY'} {route.path}")
    
    # Shutdown event
    @app.on_event("shutdown")
    async def shutdown():
        logger.info(f"Shutting down {config['title']}")
    
    return app


# Global app instance
app = create_app()
