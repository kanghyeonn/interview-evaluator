import streamlit as st
import mysql.connector
import hashlib
from datetime import datetime
from substrack_text import *


# 비밀번호 해시 함수
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed):
    return hash_password(password) == hashed

# MySQL 연결
def get_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',        # ← 본인의 MySQL 사용자명으로 수정
        password='0000',# ← 본인의 MySQL 비밀번호로 수정
        database='tooktak'
    )

# 회원가입 처리 (user + resume 함께 등록)
def register_user_with_resume(user_id, password, name, job, resume_content):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        hashed_pw = hash_password(password)

        # 사용자 등록
        cursor.execute("""
            INSERT INTO users (user_id, password, name, job)
            VALUES (%s, %s, %s, %s)
        """, (user_id, hashed_pw, name, job))
        user_db_id = cursor.lastrowid

        # 이력서 등록
        cursor.execute("""
            INSERT INTO resumes (user_id, content)
            VALUES (%s, %s)
        """, (user_db_id, resume_content))

        conn.commit()
        return True
    except Exception as e:
        print("회원가입 오류:", e)
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

# 로그인 처리
def authenticate(user_id, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, password, name FROM users WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user and verify_password(password, user[1]):
        return {"id": user[0], "name": user[2]}
    return None

# 이력서 저장
def save_resume(user_db_id, content):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO resumes (user_id, content)
        VALUES (%s, %s)
    """, (user_db_id, content))
    conn.commit()
    cursor.close()
    conn.close()

# 이력서 조회
def get_resumes(user_db_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT content, created_at FROM resumes
        WHERE user_id = %s ORDER BY created_at DESC
    """, (user_db_id,))
    resumes = cursor.fetchall()
    cursor.close()
    conn.close()
    return resumes

# Streamlit 앱 시작
def main():
    st.title("회원가입 / 로그인 시스템 + 이력서 관리")

    # 세션 초기화
    if 'user' not in st.session_state:
        st.session_state.user = None

    menu = ["로그인", "회원가입"]
    choice = st.sidebar.selectbox("메뉴", menu)

    if choice == "회원가입":
        st.subheader("회원가입")
        user_id = st.text_input("ID")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("이름")
        job = st.text_input("지원 직무")
        uploaded_file = st.file_uploader("이력서 파일 업로드", type=["txt", "pdf", "docx"])

        if st.button("회원가입"):
            if user_id and password and name and uploaded_file:
                
                resume_text = extract_text_from_file(uploaded_file)
                print(resume_text)
                if resume_text:
                    success = register_user_with_resume(user_id, password, name, job, resume_text)
                    if success:
                        st.success("회원가입 및 이력서 등록 완료! 이제 로그인하세요.")
                    else:
                        st.error("회원가입 실패: 이미 존재하는 ID이거나 입력 오류입니다.")
                else:
                    st.error("이력서 파일에서 텍스트를 추출할 수 없습니다.")
            else:
                st.warning("모든 필드와 이력서 파일을 입력해주세요.")

    # 로그인 화면
    elif choice == "로그인":
        st.subheader("로그인")
        user_id = st.text_input("ID")
        password = st.text_input("비밀번호", type="password")

        if st.button("로그인"):
            user = authenticate(user_id, password)
            if user:
                st.session_state.user = user
                st.success(f"{user['name']}님 환영합니다!")
            else:
                st.error("로그인 실패: ID 또는 비밀번호를 확인하세요.")

    # 로그인 후 이력서 작성 및 조회
    if st.session_state.user:
        st.markdown("---")
        st.subheader("📄 이력서 추가 작성")
        resume_text = st.text_area("새로운 이력서를 입력하세요")
        if st.button("이력서 제출"):
            if resume_text:
                save_resume(st.session_state.user["id"], resume_text)
                st.success("이력서가 저장되었습니다.")
            else:
                st.warning("이력서 내용을 입력해주세요.")

        st.markdown("---")
        st.subheader("📚 나의 이력서 목록")
        resumes = get_resumes(st.session_state.user["id"])
        if resumes:
            for r in resumes:
                st.write(f"- 작성일: {r[1].strftime('%Y-%m-%d %H:%M:%S')}")
                st.code(r[0])
        else:
            st.info("작성된 이력서가 없습니다.")

if __name__ == '__main__':
    main()
