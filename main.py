"""
Main entry point - runs Bot + API + Static in ONE process
"""
import os
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import config
from backend.config import API_HOST, ALLOWED_ORIGINS, API_PORT

# Import bot
from backend.bot import application as bot_app

# Import backend routes
from backend.main import app as backend_app

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot polling task
bot_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    global bot_task
    
    # Startup: Initialize and start bot
    logger.info("Starting Telegram bot polling...")
    if bot_app:
        await bot_app.initialize()
        await bot_app.start()
        bot_task = asyncio.create_task(bot_app.updater.start_polling())
    
    yield
    
    # Shutdown: Stop bot
    logger.info("Stopping Telegram bot...")
    if bot_task:
        bot_task.cancel()
        try:
            await bot_task
        except asyncio.CancelledError:
            pass
    if bot_app:
        await bot_app.stop()
        await bot_app.shutdown()

# Create main FastAPI app
app = FastAPI(
    title="Steal an Eggs",
    description="Telegram MiniApp + Bot",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include backend API routes directly (not mount)
app.include_router(backend_app.router)

# Mount frontend static files (must be last to not override API routes)
frontend_path = os.path.join(os.path.dirname(__file__), "frontend")
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")

if __name__ == "__main__":
    PORT = API_PORT
    
    print("=" * 60)
    print("🚀 Steal an Eggs Application Starting")
    print("=" * 60)
    print(f"Port: {PORT}")
    print(f"Frontend: /")
    print(f"API: /api/*")
    print(f"Bot: Running in background")
    print("=" * 60)
    
    uvicorn.run(
        "main:app",
        host=API_HOST,
        port=PORT,
        log_level="info"
    )
