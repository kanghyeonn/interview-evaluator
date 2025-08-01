# services/signup_service.py

from sqlalchemy.orm import Session
from datetime import datetime
from fastapi import UploadFile
from app.repository.user import User
from app.repository.resume import Resume
from app.services.extrack.extractor import extract_resume_text  # 통합 추출기 사용

def register_user_with_resume(
    db: Session,
    username: str,
    password: str,
    name: str,
    nickname: str,
    birthdate: str,
    desired_job: str,
    resume: UploadFile = None
) -> User:
    # 1. 이력서 텍스트 추출 (PDF or DOCX)
    resume_text = extract_resume_text(resume) if resume else ""

    # 2. 사용자 저장
    user = User(
        username=username,
        password=password,  # 실제 서비스에서는 bcrypt 해시 필요
        name=name,
        nickname=nickname,
        birthdate=datetime.strptime(birthdate, "%Y-%m-%d").date(),
        desired_job=desired_job
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # 3. 이력서 저장 (user_id 연결)
    if resume_text:
        resume_entry = Resume(
            user_id=user.id,
            filename=resume.filename,
            content=resume_text
        )
        db.add(resume_entry)
        db.commit()

    return user
