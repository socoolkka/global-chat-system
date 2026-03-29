from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional, Dict, Set
import time
from datetime import datetime

app = FastAPI()

# データ構造
chat_data: Dict[str, List[dict]] = {"global-chat": []}
online_users: Dict[str, dict] = {}
# サーバーごとの参加許可ユーザー {server_name: {username1, username2}}
server_permissions: Dict[str, Set[str]] = {"global-chat": set()}
# サーバーのオーナー {server_name: owner_username}
server_owners: Dict[str, str] = {}
# ユーザーごとの招待状 {username: [{"from": str, "server": str}]}
invites: Dict[str, List[dict]] = {}

class Message(BaseModel):
    username: str
    content: str
    target: str = "global-chat"
    is_dm: bool = False
    is_sticker: bool = False
    game_name: Optional[str] = "Unknown Game"
    place_id: Optional[int] = None
    job_id: Optional[str] = None
    reply_to: Optional[str] = None
    reply_content: Optional[str] = None

class NewServer(BaseModel):
    name: str
    owner: str

class KickRequest(BaseModel):
    server: str
    owner: str
    target_user: str

class InviteRequest(BaseModel):
    server: str
    from_user: str
    to_user: str

@app.get("/")
def read_root():
    return {"status": "Chat API v11 (Kick System) is running!"}

@app.get("/my_servers")
def get_my_servers(username: str):
    allowed = ["global-chat"]
    for srv, users in server_permissions.items():
        if username in users:
            allowed.append(srv)
    return {"servers": allowed}

@app.post("/create_server")
def create_server(server: NewServer):
    name = server.name.lower().replace(" ", "-")
    if name not in server_permissions:
        server_permissions[name] = {server.owner}
        server_owners[name] = server.owner
        chat_data[name] = []
    return {"status": "created", "name": name}

@app.post("/kick_user")
def kick_user(req: KickRequest):
    # オーナー確認
    if server_owners.get(req.server) == req.owner:
        if req.target_user in server_permissions.get(req.server, set()):
            server_permissions[req.server].remove(req.target_user)
            return {"status": "kicked", "user": req.target_user}
    return {"status": "error", "message": "Unauthorized or User not found"}

@app.post("/send_invite")
def send_invite(req: InviteRequest):
    if req.to_user not in invites:
        invites[req.to_user] = []
    if not any(i["server"] == req.server for i in invites[req.to_user]):
        invites[req.to_user].append({"from": req.from_user, "server": req.server})
    return {"status": "invited"}

@app.get("/check_invites")
def check_invites(username: str):
    return {"invites": invites.get(username, [])}

@app.post("/accept_invite")
def accept_invite(username: str, server: str):
    if server in server_permissions:
        server_permissions[server].add(username)
    if username in invites:
        invites[username] = [i for i in invites[username] if i["server"] != server]
    return {"status": "accepted"}

@app.get("/messages")
def get_messages(username: str, target: str = "global-chat", is_dm: bool = False, game_name: str = "Unknown", place_id: int = 0, job_id: str = ""):
    online_users[username] = {"time": time.time(), "game_name": game_name, "place_id": place_id, "job_id": job_id}
    room_id = target
    if is_dm:
        users = sorted([username, target])
        room_id = f"dm_{users[0]}_{users[1]}"
    
    if not is_dm and room_id != "global-chat":
        if username not in server_permissions.get(room_id, set()):
            return {"messages": [], "online_users": {}, "error": "No Permission"}

    current_time = time.time()
    active_users = {u: info for u, info in online_users.items() if current_time - info["time"] < 20}
    return {"messages": chat_data.get(room_id, []), "online_users": active_users, "room_id": room_id}

@app.post("/send")
async def send_message(msg: Message):
    room_id = msg.target
    if msg.is_dm:
        users = sorted([msg.username, msg.target])
        room_id = f"dm_{users[0]}_{users[1]}"
    if room_id not in chat_data:
        chat_data[room_id] = []
    new_msg = {"username": msg.username, "content": msg.content, "timestamp": datetime.now().strftime("%H:%M"), "is_sticker": msg.is_sticker, "game_name": msg.game_name, "place_id": msg.place_id, "job_id": msg.job_id, "reply_to": msg.reply_to, "reply_content": msg.reply_content, "is_dm": msg.is_dm}
    chat_data[room_id].append(new_msg)
    if len(chat_data[room_id]) > 100: chat_data[room_id].pop(0)
    return {"status": "sent", "room": room_id}
