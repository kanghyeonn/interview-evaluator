from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from jose import jwt
from app.repository.user import User
import os

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"

def authenticate_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if not user or user.password != password:
        return None

    # JWT 토큰 생성
    payload = {
        "sub": str(user.id),
        "exp": datetime.now(timezone.utc) + timedelta(hours=12)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id
    }
