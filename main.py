from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from datetime import datetime, timedelta

app = FastAPI()

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # すべてのオリジンからのアクセスを許可（本番環境では特定のオリジンに制限することを推奨）
    allow_credentials=True,
    allow_methods=["*"],  # すべてのHTTPメソッドを許可
    allow_headers=["*"],  # すべてのHTTPヘッダーを許可
)

class Message(BaseModel):
    username: str
    content: str

class StoredMessage(Message):
    timestamp: str # 表示用のフォーマットされた日時
    created_at: datetime # 内部処理用の正確な日時

# 最新のメッセージを保持するリスト（メモリ内）
messages: List[StoredMessage] = []
MAX_MESSAGES = 50  # 保持する最大メッセージ数
MESSAGE_LIFETIME_HOURS = 24 # メッセージの保持期間（時間）

@app.get("/")
async def read_root():
    return {"message": "Chat API is running!"}

@app.get("/messages", response_model=List[StoredMessage])
async def get_messages():
    # 24時間以上経過したメッセージをフィルタリング
    global messages
    now = datetime.now()
    messages = [msg for msg in messages if now - msg.created_at < timedelta(hours=MESSAGE_LIFETIME_HOURS)]
    return messages

@app.post("/send")
async def send_message(message: Message):
    now = datetime.now()
    # 表示用の日時フォーマット (例: 03/28 15:30)
    formatted_timestamp = now.strftime("%m/%d %H:%M")
    
    stored_message = StoredMessage(
        username=message.username,
        content=message.content,
        timestamp=formatted_timestamp,
        created_at=now
    )
    messages.append(stored_message)

    # 古いメッセージを削除（MAX_MESSAGESを超えた場合）
    if len(messages) > MAX_MESSAGES:
        messages.pop(0) # 最も古いメッセージを削除

    return {"success": True, "message": stored_message}
