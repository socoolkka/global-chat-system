from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging

# ログの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# メッセージのデータモデル
class Message(BaseModel):
    username: str
    content: str
    reply_to: Optional[str] = None
    reply_content: Optional[str] = None

class StoredMessage(Message):
    timestamp: str
    created_at: datetime

# メモリ内データ保持
messages_list: List[StoredMessage] = []
user_last_seen: Dict[str, datetime] = {}

# 定数
MAX_MESSAGES = 100
MESSAGE_LIFETIME_HOURS = 24
ONLINE_THRESHOLD_SECONDS = 20

@app.get("/")
async def root():
    # バージョン表示を v4 に更新
    return {"message": "Chat API v4 is running!", "status": "ok"}

@app.get("/messages")
async def get_messages(username: Optional[str] = None):
    now = datetime.now()
    if username:
        user_last_seen[username] = now
    
    global messages_list
    messages_list = [
        m for m in messages_list 
        if now - m.created_at < timedelta(hours=MESSAGE_LIFETIME_HOURS)
    ]
    
    online_users = [
        u for u, last_seen in user_last_seen.items() 
        if now - last_seen < timedelta(seconds=ONLINE_THRESHOLD_SECONDS)
    ]
    
    return {
        "messages": messages_list,
        "online_users": online_users
    }

@app.post("/send")
async def send_message(message: Message):
    try:
        now = datetime.now()
        user_last_seen[message.username] = now
        
        stored_message = StoredMessage(
            username=message.username,
            content=message.content,
            reply_to=message.reply_to,
            reply_content=message.reply_content,
            timestamp=now.strftime("%m/%d %H:%M"),
            created_at=now
        )
        
        messages_list.append(stored_message)
        if len(messages_list) > MAX_MESSAGES:
            messages_list.pop(0)
            
        logger.info(f"v4: Message from {message.username}")
        return {"success": True}
    except Exception as e:
        logger.error(f"Error in v4 send_message: {e}")
        return {"success": False, "error": str(e)}
