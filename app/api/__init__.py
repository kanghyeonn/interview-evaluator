from .audio import router as audio_router
from .video import router as video_router
from .signup import router as signup_router

__all__ = ["audio_router", "video_router", "signup_router"]