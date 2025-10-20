"""FastAPI application entry point."""

import os
import time
import json
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from province.api.routes import api_router
from province.core.config import get_settings
from province.core.logging import setup_logging
from province.agents.agent_service import register_tax_agents

# Load environment variables from .env.local
load_dotenv('.env.local')

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    # Startup
    setup_logging()
    logger.info("=" * 80)
    logger.info("🚀 Province Tax Filing Backend Starting Up")
    logger.info("=" * 80)
    logger.info("Environment", environment=os.getenv('ENVIRONMENT', 'development'))
    logger.info("AWS Region", region=os.getenv('AWS_REGION', 'us-east-1'))
    logger.info("Debug Mode", debug=os.getenv('DEBUG', 'true'))
    
    # Register tax agents
    logger.info("📋 Registering tax agents...")
    register_tax_agents()
    logger.info("✅ Tax agents registered successfully")
    
    # Log available routes
    logger.info("📍 API Routes available at /api/v1")
    logger.info("📖 API Documentation available at /docs")
    logger.info("🎯 Health check available at /health")
    logger.info("=" * 80)
    logger.info("✅ Backend Ready - Listening on http://0.0.0.0:8000")
    logger.info("=" * 80)
    
    yield
    
    # Shutdown
    logger.info("=" * 80)
    logger.info("🛑 Province Tax Filing Backend Shutting Down")
    logger.info("=" * 80)


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title="Province Tax Filing Backend",
        description="AI-powered tax filing system with conversational agent",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url="/redoc" if settings.environment != "production" else None,
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Request/Response logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """Log all incoming requests and outgoing responses with detailed info."""
        request_id = str(time.time())
        start_time = time.time()
        
        # Log incoming request
        logger.info(
            "📨 INCOMING REQUEST",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            query_params=dict(request.query_params),
            client=request.client.host if request.client else "unknown",
        )
        
        # Log request body for POST/PUT/PATCH
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    try:
                        body_json = json.loads(body.decode())
                        # Hide sensitive fields
                        safe_body = {k: v if k not in ['password', 'ssn', 'account_number', 'routing_number'] else '***' 
                                    for k, v in body_json.items()}
                        logger.info(
                            "📝 Request Body",
                            request_id=request_id,
                            body=safe_body
                        )
                    except:
                        logger.info(
                            "📝 Request Body",
                            request_id=request_id,
                            body_size=len(body)
                        )
                # Reset body for next middleware
                async def receive():
                    return {"type": "http.request", "body": body}
                request._receive = receive
            except Exception as e:
                logger.error("Error reading request body", error=str(e))
        
        # Process request
        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000
            
            # Log successful response
            logger.info(
                "✅ REQUEST COMPLETE",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=f"{duration_ms:.2f}ms"
            )
            
            return response
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            # Log error
            logger.error(
                "❌ REQUEST FAILED",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                error=str(e),
                error_type=type(e).__name__,
                duration_ms=f"{duration_ms:.2f}ms"
            )
            
            # Return error response
            return JSONResponse(
                status_code=500,
                content={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "request_id": request_id
                }
            )
    
    # Include API routes
    app.include_router(api_router, prefix="/api/v1")
    
    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint with service information."""
        return {
            "service": "Province Tax Filing Backend",
            "version": "0.1.0",
            "status": "running",
            "docs": "/docs",
            "api": "/api/v1"
        }
    
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(
        "province.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development",
        log_config=None,  # Use our custom logging
    )