from fastapi import FastAPI
from app.api import audio_router 
from app.api import video_router

app = FastAPI()

# WebSocket 라우터 포함
app.include_router(audio_router)
app.include_router(video_router)