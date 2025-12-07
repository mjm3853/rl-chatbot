"""FastAPI application entry point."""

import uvicorn
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .database import init_db
from .routers import agents, test_cases, health, chat, conversations, evaluations, training, tools

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    await init_db()
    yield
    # Shutdown
    pass


app = FastAPI(
    title="RL Chatbot API",
    description="API for managing, evaluating, and training RL chatbot agents",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])
app.include_router(test_cases.router, prefix="/api/v1/test-cases", tags=["test-cases"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(conversations.router, prefix="/api/v1/conversations", tags=["conversations"])
app.include_router(evaluations.router, prefix="/api/v1/evaluations", tags=["evaluations"])
app.include_router(training.router, prefix="/api/v1/training", tags=["training"])
app.include_router(tools.router, prefix="/api/v1/tools", tags=["tools"])


def run():
    """Run the server."""
    uvicorn.run(
        "rl_chatbot.server.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )


if __name__ == "__main__":
    run()
