from fastapi import FastAPI
from app.api import audio_router  # __init__.py에서 import된 router 사용
from app.api import video_router

app = FastAPI()

# WebSocket 라우터 포함
app.include_router(audio_router)
app.include_router(video_router)