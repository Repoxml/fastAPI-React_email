from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from jose import jwt, JWTError
from passlib.context import CryptContext
from contextlib import asynccontextmanager
from database import init_db, get_user, create_user, get_all_users, create_message, get_messages_for_user
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi import WebSocket, WebSocketDisconnect
from manager import WebSocketManager
import os
from dotenv import load_dotenv

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY not set in .env")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

app = FastAPI(title="JWT Auth Demo (SQLite)", lifespan=lifespan)
manager = WebSocketManager()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/chat")
def serve_chat():
    return FileResponse("templates/index.html")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=20)
    password: str = Field(..., min_length=6)

class UserPublic(BaseModel):
    username: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class MessageCreate(BaseModel):
    title: str
    context: str
    recipients: list[str]


def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict, expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def authenticate_user(username: str, password: str) -> Optional[dict]:
    user = get_user(username)
    if not user or not verify_password(password, user["hashed_password"]):
        return None
    return user


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserPublic:
    cred_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub")
        if username is None:
            raise cred_exc
    except JWTError:
        raise cred_exc

    user = get_user(username)
    if not user:
        raise cred_exc
    return UserPublic(username=user["username"])


@app.post("/register", status_code=201, summary="Create a new user")
def register_user(body: UserCreate):
    hashed = hash_password(body.password)
    create_user(body.username, hashed)
    return {"message": "User registered successfully"}


@app.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token({"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/me", response_model=UserPublic, summary="Get my profile (protected)")
def read_me(current_user: UserPublic = Depends(get_current_user)):
    return current_user

@app.get("/users", response_model=list[str], summary="Get all users (protected)")
def read_users(current_user: UserPublic = Depends(get_current_user)):
    all_users = get_all_users()
    return [u for u in all_users if u != current_user.username]

@app.post("/messages", status_code=201, summary="Send a new message")
def send_message(
    body: MessageCreate,
    current_user: UserPublic = Depends(get_current_user)
):
    message_id = create_message(
        sender=current_user.username,
        title=body.title,
        context=body.context,
        recipients=body.recipients,
    )
    return {"id": message_id, "message": "Message sent"}

@app.get("/messages", response_model=list[dict], summary="Get my messages (self and received)")
def get_messages(current_user: UserPublic = Depends(get_current_user)):
    messages = get_messages_for_user(current_user.username)
    return messages

@app.on_event("startup")
def on_startup():
    init_db()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    token = websocket.query_params.get('token')
    
    if not token:
        await websocket.close(code=1008)
        return
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            await websocket.close(code=1008)
            return
    except JWTError:
        await websocket.close(code=1008)
        return
    
    print(f"user connected: {username}")
    
    await manager.connect(websocket, username)
    while True:
        try:
            message = await websocket.receive_json()
            print(f"received message: {message}")
            recipients = message.get("recipients", [])
            for client_ws, client_username in manager.connected_clients.items():
                if client_username in recipients or client_username == username:
                    await manager.send_message(client_ws, message, username)
        except WebSocketDisconnect:
            await manager.disconnect(websocket)
            break