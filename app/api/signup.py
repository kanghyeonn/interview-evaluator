from fastapi import APIRouter, UploadFile, Form, File, Depends
from sqlalchemy.orm import Session
from app.repository.database import SessionLocal
from app.services.user.signup_service import register_user_with_resume

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/signup")
async def signup(
    username: str = Form(...),
    password: str = Form(...),
    name: str = Form(...),
    nickname: str = Form(...),
    birthdate: str = Form(...),
    desiredJob: str = Form(...),
    resume: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    user = register_user_with_resume(
        db=db,
        username=username,
        password=password,
        name=name,
        nickname=nickname,
        birthdate=birthdate,
        desired_job=desiredJob,
        resume=resume
    )
    return {"message": f"{username}님 가입 완료!", "user_id": user.id}
