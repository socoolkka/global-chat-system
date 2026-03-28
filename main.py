from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging

# エラーログを表示するように設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# CORS設定（Robloxからの通信を許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# データモデル
class Message(BaseModel):
    username: str
    content: str

class StoredMessage(Message):
    timestamp: str
    created_at: datetime

# メモリ内データ保持
messages_list: List[StoredMessage] = []
user_last_seen: Dict[str, datetime] = {}

# 定数
MAX_MESSAGES = 100
MESSAGE_LIFETIME_HOURS = 24
ONLINE_THRESHOLD_SECONDS = 20 # 20秒以内に通信があればオンライン

@app.get("/")
async def root():
    return {"message": "Chat API is running!", "status": "ok"}

@app.get("/messages")
async def get_messages(username: Optional[str] = None):
    try:
        now = datetime.now()
        
        # 通信があったユーザーのアクティブ時間を更新
        if username:
            user_last_seen[username] = now
            logger.info(f"User active: {username}")
        
        # 24時間経過したメッセージを削除
        global messages_list
        messages_list = [msg for msg in messages_list if now - msg.created_at < timedelta(hours=MESSAGE_LIFETIME_HOURS)]
        
        # オンラインユーザーのリストを作成
        online_users = [
            u for u, last_seen in user_last_seen.items() 
            if now - last_seen < timedelta(seconds=ONLINE_THRESHOLD_SECONDS)
        ]
        
        # メッセージを辞書形式に変換して返す
        return {
            "messages": [
                {"username": m.username, "content": m.content, "timestamp": m.timestamp} 
                for m in messages_list
            ],
            "online_users": online_users
        }
    except Exception as e:
        logger.error(f"Error in get_messages: {e}")
        return {"messages": [], "online_users": [], "error": str(e)}

@app.post("/send")
async def send_message(message: Message):
    try:
        now = datetime.now()
        # 送信者もオンラインとして記録
        user_last_seen[message.username] = now
        
        new_msg = StoredMessage(
            username=message.username,
            content=message.content,
            timestamp=now.strftime("%m/%d %H:%M"),
            created_at=now
        )
        
        messages_list.append(new_msg)
        
        # 最大数を超えたら古いものを削除
        if len(messages_list) > MAX_MESSAGES:
            messages_list.pop(0)
            
        logger.info(f"Message sent by {message.username}")
        return {"success": True}
    except Exception as e:
        logger.error(f"Error in send_message: {e}")
        return {"success": False, "error": str(e)}
