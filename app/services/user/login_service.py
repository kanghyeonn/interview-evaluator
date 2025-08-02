from sqlalchemy.orm import Session
from app.repository.user import User
from app.core.security import create_access_token

def authenticate_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if not user or user.password != password:
        return None

    access_token = create_access_token(user_id=user.id)
    return {
        "access_token": access_token,
        "user_id": user.id
    }
