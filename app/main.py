from fastapi import FastAPI
from app.api import audio_router 
from app.api import video_router
from app.api import signup_router
from app.api import check_username_router
from app.api import login_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# ✅ CORS 설정 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 개발 환경에선 Next.js 주소
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# WebSocket 라우터 포함
app.include_router(audio_router)
app.include_router(video_router)
app.include_router(signup_router)
app.include_router(check_username_router)
app.include_router(login_router)