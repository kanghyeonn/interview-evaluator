from fastapi import APIRouter, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from app.repository.database import SessionLocal
from app.services.user.login_service import authenticate_user
from pydantic import BaseModel

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class LoginInput(BaseModel):
    username: str
    password: str

@router.post("/login")
def login(data: LoginInput, db: Session = Depends(get_db)):
    token_data = authenticate_user(db=db, username=data.username, password=data.password)
    if not token_data:
        raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 올바르지 않습니다.")
    print(token_data)
    return token_data

