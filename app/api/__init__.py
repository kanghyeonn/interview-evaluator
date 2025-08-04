from .audio import router as audio_router
from .video import router as video_router
from .signup import router as signup_router
from .user import router as user_router
from .interview import router as interview_router
from .questionresult import router as questionresult_router

__all__ = ["audio_router", "video_router", "signup_router", "user_router", "interview_router", "questionresult_router"]
