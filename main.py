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
user_status: Dict[str, datetime] = {}

MAX_MESSAGES = 100
MESSAGE_LIFETIME_HOURS = 24
ONLINE_THRESHOLD_SECONDS = 15 # 少し余裕を持たせて15秒に設定

# 稼働確認用（ブラウザで開いた時に表示される）
@app.get("/")
async def read_root():
    return {"message": "Chat API is running!"}

# メッセージ取得用
@app.get("/messages")
async def get_messages(username: str = None):
    now = datetime.now()
    
    # 通信があったユーザーのアクティブ時間を更新
    if username:
        user_status[username] = now
    
    # 24時間経過メッセージ削除
    global messages
    messages = [msg for msg in messages if now - msg.created_at < timedelta(hours=MESSAGE_LIFETIME_HOURS)]
    
    # オンラインユーザーのリストを作成
    online_users = [
        u for u, last_seen in user_status.items() 
        if now - last_seen < timedelta(seconds=ONLINE_THRESHOLD_SECONDS)
    ]
    
    # リスト形式でメッセージを返す（以前の形式と互換性を保つ）
    return {
        "messages": messages,
        "online_users": online_users
    }

@app.post("/send")
async def send_message(message: Message):
    now = datetime.now()
    user_status[message.username] = now
    
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
