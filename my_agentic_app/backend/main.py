"""
Main entry point for the FastAPI application.
Assembles routers, middleware, and application state.
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.line_webhook import router as line_webhook_router
from backend.api.user_api import router as user_api_router

# Configure basic logging
logging.basicConfig(level=logging.INFO)

def create_app() -> FastAPI:
    """
    Application factory function.
    
    Returns:
        FastAPI: The configured FastAPI application instance.
    """
    app = FastAPI(
        title="AI Operation Management System",
        description="Gateway service and Agentic core for operations management.",
        version="1.0.0"
    )

    app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    )

    # Register routers
    # Prefix is optional, but good for versioning e.g., /api/v1/line/webhook
    app.include_router(line_webhook_router, prefix="/api/v1/line", tags=["LINE Webhook"])
    app.include_router(user_api_router, prefix="/api/users", tags=["Users"])

    @app.get("/health")
    async def health_check():
        """
        Simple health check endpoint for monitoring.
        """
        return {"status": "healthy"}

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    # Run the application using Uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)