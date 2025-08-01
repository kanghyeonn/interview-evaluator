from .audio import router as audio_router
from .video import router as video_router
from .signup import router as signup_router
from .check_username import router as check_username_router
from .login import router as login_router

__all__ = ["audio_router", "video_router", "signup_router", "check_username_router", "login_router"]