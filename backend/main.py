"""
Python FastAPI Backend for Telegram MiniApp
Handles TP (TelegramPlatform) resources, clicks, and verification
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import json
import logging
import httpx

from . import config

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Steal an Eggs API",
    description="Backend API for Telegram MiniApp",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for user progress (use Redis/DB in production)
user_progress = {}

# ==================== Pydantic Models ====================

class ResourcesRequest(BaseModel):
    init_data: Optional[str] = ""

class ClickRequest(BaseModel):
    init_data: Optional[str] = ""

class VerifyRequest(BaseModel):
    init_data: Optional[str] = ""

class CheckSubscriptionRequest(BaseModel):
    user_id: Optional[int] = None

# ==================== Helper Functions ====================

def parse_init_data(init_data: str) -> Optional[dict]:
    """Parse Telegram initData to extract user_id"""
    try:
        params = dict(pair.split('=', 1) for pair in init_data.split('&') if '=' in pair)
        user_json = params.get('user')
        if user_json:
            user = json.loads(user_json)
            return {"user_id": user.get("id"), "username": user.get("username")}
    except Exception as e:
        logger.error(f"Failed to parse initData: {e}")
    return None

def find_channel_by_resource_id(resource_id: int) -> Optional[dict]:
    """Find channel by resource_id"""
    for channel in config.CHANNELS:
        if channel.get("tp_resource_id") == resource_id:
            return channel
    return None

async def check_subscription_real(chat_id: str, user_id: int, bot_token: str) -> bool:
    """Check subscription via Telegram Bot API"""
    try:
        url = f"https://api.telegram.org/bot{bot_token}/getChatMember"
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json={
                "chat_id": chat_id,
                "user_id": user_id
            })
            data = response.json()
            
            if data.get("ok"):
                status = data.get("result", {}).get("status")
                return status in ["member", "administrator", "creator"]
    except Exception as e:
        logger.error(f"Subscription check failed: {e}")
    return False

# ==================== API Endpoints ====================

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "tp_mode": config.TP_MODE
    }

@app.get("/api/config")
async def get_config():
    """Get public configuration for frontend"""
    return {
        "app_title": config.APP_TITLE,
        "app_description": config.APP_DESCRIPTION,
        "button_color": config.BUTTON_COLOR,
        "button_color_hex": config.BUTTON_COLOR_HEX,
        "reward_label": config.REWARD_LABEL,
        "share_text": config.SHARE_TEXT,
        "share_url": config.SHARE_URL
    }

@app.post("/api/tp/resources/{bot_id}")
async def get_resources(bot_id: int, request: ResourcesRequest):
    """
    Get resources (sponsors list)
    POST /tp/resources/:bot_id
    """
    logger.info(f"[Resources] Request for bot_id: {bot_id}")
    
    # Get fresh channels from file
    channels = config.get_channels()
    
    # Get channels that should be verified
    verify_resource_ids = config.VERIFY_RESOURCE_IDS if config.VERIFY_RESOURCE_IDS else [
        ch["tp_resource_id"] for ch in channels if ch.get("require_verify")
    ]
    
    sponsors = [
        {
            "url": ch["url"],
            "name": ch["name"],
            "desc": ch["desc"],
            "tp_bot_id": ch["tp_bot_id"],
            "tp_flow_id": ch["tp_flow_id"],
            "tp_resource_id": ch["tp_resource_id"],
            "tp_type": ch["tp_type"],
            "tp_target_action": ch["tp_target_action"],
            "tp_verification_mode": ch["tp_verification_mode"]
        }
        for ch in channels
    ]
    
    verify = [
        {
            "tp_bot_id": ch["tp_bot_id"],
            "tp_flow_id": ch["tp_flow_id"],
            "tp_resource_id": ch["tp_resource_id"],
            "name": ch["name"]
        }
        for ch in channels
        if ch["tp_resource_id"] in verify_resource_ids
    ]
    
    return {
        "sponsors": sponsors,
        "verify": verify,
        "mode": "tp" if config.TP_MODE else "normal"
    }

@app.post("/api/tp/click/{bot_id}/{flow_id}/{resource_id}")
async def handle_click(bot_id: int, flow_id: int, resource_id: int, request: ClickRequest):
    """
    Handle click on sponsor (return target URL)
    POST /tp/click/:bot_id/:flow_id/:resource_id
    """
    logger.info(f"[Click] bot_id: {bot_id}, flow_id: {flow_id}, resource_id: {resource_id}")
    
    channel = find_channel_by_resource_id(resource_id)
    
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    # CRITICAL: Must return "target_url" (not just "url") for frontend to work
    return {
        "ok": True,
        "target_url": channel["url"],
        "completed": False
    }

@app.post("/api/tp/verify/{bot_id}/{flow_id}/{resource_id}")
async def verify_subscription(bot_id: int, flow_id: int, resource_id: int, request: VerifyRequest):
    """
    Verify subscription
    POST /tp/verify/:bot_id/:flow_id/:resource_id
    """
    logger.info(f"[Verify] bot_id: {bot_id}, flow_id: {flow_id}, resource_id: {resource_id}")
    
    channel = find_channel_by_resource_id(resource_id)
    
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    verified = False
    
    # Determine verification result based on fallback mode
    if config.VERIFY_FALLBACK == "always_ok":
        verified = True
        logger.info(f"[Verify] Always OK mode - resource_id: {resource_id}")
    elif config.VERIFY_FALLBACK == "always_fail":
        verified = False
        logger.info(f"[Verify] Always Fail mode - resource_id: {resource_id}")
    elif config.VERIFY_FALLBACK == "real" and config.BOT_TOKEN:
        # Real verification via Bot API
        user_data = parse_init_data(request.init_data)
        if user_data and user_data.get("user_id"):
            verified = await check_subscription_real(
                channel["chat_id"],
                user_data["user_id"],
                config.BOT_TOKEN
            )
            logger.info(f"[Verify] Real check - user: {user_data['user_id']}, verified: {verified}")
        else:
            logger.info("[Verify] Could not parse user_id from init_data")
            verified = False
    else:
        # No token or unknown mode - default to fail
        verified = False
    
    return {
        "ok": True,
        "verified": verified,
        "resource_id": resource_id
    }

@app.post("/api/check_subscription/{bot_id}")
async def check_subscription(bot_id: int, request: CheckSubscriptionRequest):
    """
    General subscription check
    POST /api/check_subscription/:bot_id
    """
    logger.info(f"[Check Subscription] bot_id: {bot_id}, user_id: {request.user_id}")
    
    # For demo purposes, return subscribed: true
    # In production, check all required channels
    return {
        "ok": True,
        "subscribed": True
    }

# ==================== Progress Tracking Endpoints ====================

@app.post("/api/progress/get")
async def get_progress(request: Request):
    """Get user progress (restore on app reopen)"""
    body = await request.json()
    init_data = body.get("init_data")
    user_id = body.get("user_id")
    
    if not user_id and init_data:
        user_data = parse_init_data(init_data)
        user_id = user_data.get("user_id") if user_data else None
    
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id required")
    
    progress = user_progress.get(user_id, {
        "currentStage": "egg-selection",
        "selectedEgg": None,
        "prizeMultiplier": None,
        "robloxUsername": None,
        "sharedWithFriends": False,
        "verifiedChannels": [],
        "lastUpdated": None
    })
    
    logger.info(f"[Get Progress] user: {user_id}, stage: {progress.get('currentStage')}")
    
    return {
        "ok": True,
        "progress": progress
    }

@app.post("/api/progress/update")
async def update_progress(request: Request):
    """Update user progress (save progress)"""
    body = await request.json()
    init_data = body.get("init_data")
    user_id = body.get("user_id")
    updates = body.get("updates", {})
    
    if not user_id and init_data:
        user_data = parse_init_data(init_data)
        user_id = user_data.get("user_id") if user_data else None
    
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id required")
    
    if user_id not in user_progress:
        user_progress[user_id] = {}
    
    user_progress[user_id].update(updates)
    
    logger.info(f"[Update Progress] user: {user_id}, updates: {updates}")
    
    return {
        "ok": True,
        "progress": user_progress[user_id]
    }

@app.post("/api/progress/reset")
async def reset_progress(request: Request):
    """Reset user progress (for testing)"""
    body = await request.json()
    user_id = body.get("user_id")
    
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id required")
    
    if user_id in user_progress:
        del user_progress[user_id]
    
    logger.info(f"[Reset Progress] user: {user_id}")
    
    return {
        "ok": True,
        "message": "Progress reset"
    }

# ==================== Start Server ====================

if __name__ == "__main__":
    import uvicorn
    import os
    
    PORT = int(os.environ.get("PORT", 8000))
    
    print("=" * 60)
    print("🚀 Telegram MiniApp Backend Started")
    print("=" * 60)
    print(f"Server running on: http://localhost:{PORT}")
    print(f"Bot ID: {config.BOT_ID}")
    print(f"Verification Mode: {config.VERIFY_FALLBACK}")
    print(f"Channels configured: {len(config.CHANNELS)}")
    print("=" * 60)
    print()
    print("📋 Available endpoints:")
    print(f"  POST /tp/resources/{config.BOT_ID}")
    print(f"  POST /tp/click/{config.BOT_ID}/:flow_id/:resource_id")
    print(f"  POST /tp/verify/{config.BOT_ID}/:flow_id/:resource_id")
    print(f"  POST /api/check_subscription/{config.BOT_ID}")
    print("  POST /api/progress/get")
    print("  POST /api/progress/update")
    print("  POST /api/progress/reset")
    print("  GET  /api/config")
    print("  GET  /health")
    print("=" * 60)
    print()
    print("⚙️  Configuration:")
    for i, ch in enumerate(config.CHANNELS, 1):
        print(f"  {i}. {ch['name']} (ID: {ch['tp_resource_id']}) - {ch['tp_type']}")
    print("=" * 60)
    
    uvicorn.run(
        "main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=True
    )
