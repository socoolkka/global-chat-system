from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime, timedelta

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Message(BaseModel):
    username: str
    content: str

class StoredMessage(Message):
    timestamp: str
    created_at: datetime

# データ保持
messages: List[StoredMessage] = []
user_status: Dict[str, datetime] = {} # ユーザー名: 最終アクティブ時間

MAX_MESSAGES = 100
MESSAGE_LIFETIME_HOURS = 24
ONLINE_THRESHOLD_SECONDS = 10 # 10秒以内に通信があればオンライン

@app.get("/messages")
async def get_messages(username: str = None):
    # 通信があったユーザーのアクティブ時間を更新
    if username:
        user_status[username] = datetime.now()
    
    # 24時間経過メッセージ削除
    global messages
    now = datetime.now()
    messages = [msg for msg in messages if now - msg.created_at < timedelta(hours=MESSAGE_LIFETIME_HOURS)]
    
    # オンラインユーザーのリストを作成
    online_users = [
        u for u, last_seen in user_status.items() 
        if now - last_seen < timedelta(seconds=ONLINE_THRESHOLD_SECONDS)
    ]
    
    return {
        "messages": messages,
        "online_users": online_users
    }

@app.post("/send")
async def send_message(message: Message):
    now = datetime.now()
    user_status[message.username] = now # 送信時もアクティブ更新
    
    stored_message = StoredMessage(
        username=message.username,
        content=message.content,
        timestamp=now.strftime("%m/%d %H:%M"),
        created_at=now
    )
    messages.append(stored_message)
    if len(messages) > MAX_MESSAGES:
        messages.pop(0)
    return {"success": True}
