from fastapi import APIRouter, UploadFile, Form, File, Depends
from sqlalchemy.orm import Session
from app.repository.database import SessionLocal
from app.repository.user import User
from datetime import datetime
import os
from docx import Document
import pdfplumber

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def extract_text_from_docx(uploaded_file: UploadFile) -> str:
    contents = uploaded_file.file.read()
    temp_path = "temp.docx"
    with open(temp_path, "wb") as f:
        f.write(contents)

    doc = Document(temp_path)
    os.remove(temp_path)

    return "\n".join(p.text for p in doc.paragraphs)

# pdf 파일에서 파일을 읽어 text를 추출하는 함수
def extract_text_from_pdf(file_obj) -> str:
    full_text = ""
    with pdfplumber.open(file_obj) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"
    return full_text.strip()

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
    resume_text = ""
    if resume and resume.filename.endswith(".docx"):
        resume_text = extract_text_from_docx(resume)
    elif resume and resume.filename.endswith(".pdf"):
        resume_text = extract_text_from_pdf(resume.file)

    user = User(
        username=username,
        password=password,  # 실제 운영에선 bcrypt로 해싱하세요
        name=name,
        nickname=nickname,
        birthdate=datetime.strptime(birthdate, "%Y-%m-%d").date(),
        desired_job=desiredJob,
        resume_text=resume_text
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": f"{username}님 가입 완료!"}
