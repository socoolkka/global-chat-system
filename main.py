from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional, Dict
import time
from datetime import datetime

app = FastAPI()

# データ構造
chat_data: Dict[str, List[dict]] = {"global-chat": []}
online_users: Dict[str, dict] = {} # {username: {"time": float, "game_name": str, "place_id": int, "job_id": str}}

class Message(BaseModel):
    username: str
    content: str
    target: str = "global-chat"
    is_dm: bool = False
    is_sticker: bool = False
    game_name: Optional[str] = "Unknown Game" # ゲーム名を追加
    place_id: Optional[int] = None
    job_id: Optional[str] = None
    reply_to: Optional[str] = None
    reply_content: Optional[str] = None

@app.get("/")
def read_root():
    return {"status": "Chat API v8 (Game Names & JobId) is running!"}

@app.get("/messages")
def get_messages(username: str, target: str = "global-chat", is_dm: bool = False, game_name: str = "Unknown", place_id: int = 0, job_id: str = ""):
    # ユーザーのステータスを更新
    online_users[username] = {
        "time": time.time(),
        "game_name": game_name,
        "place_id": place_id,
        "job_id": job_id
    }
    
    room_id = target
    if is_dm:
        users = sorted([username, target])
        room_id = f"dm_{users[0]}_{users[1]}"
    
    if room_id not in chat_data:
        chat_data[room_id] = []
        
    current_time = time.time()
    active_users = {u: info for u, info in online_users.items() if current_time - info["time"] < 20}
    
    return {
        "messages": chat_data.get(room_id, []),
        "online_users": active_users,
        "room_id": room_id
    }

@app.post("/send")
async def send_message(msg: Message):
    room_id = msg.target
    if msg.is_dm:
        users = sorted([msg.username, msg.target])
        room_id = f"dm_{users[0]}_{users[1]}"
        
    if room_id not in chat_data:
        chat_data[room_id] = []
        
    new_msg = {
        "username": msg.username,
        "content": msg.content,
        "timestamp": datetime.now().strftime("%H:%M"),
        "is_sticker": msg.is_sticker,
        "game_name": msg.game_name,
        "place_id": msg.place_id,
        "job_id": msg.job_id,
        "reply_to": msg.reply_to,
        "reply_content": msg.reply_content,
        "is_dm": msg.is_dm
    }
    
    chat_data[room_id].append(new_msg)
    if len(chat_data[room_id]) > 100:
        chat_data[room_id].pop(0)
        
    return {"status": "sent", "room": room_id}
