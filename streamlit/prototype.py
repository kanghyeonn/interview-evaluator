import streamlit as st
import pymysql
import bcrypt
from dummydata import *
import pandas as pd

# --- DB 연결 함수 ---
def get_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='ankh6425',
        database='test',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

# --- 유틸 함수 ---
def user_exists(username):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
            return cursor.fetchone() is not None

def register_user(username, password):
    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", (username, hashed_pw))
        conn.commit()

def login_user(username, password):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT password_hash FROM users WHERE username=%s", (username,))
            user = cursor.fetchone()
            if user and bcrypt.checkpw(password.encode(), user['password_hash'].encode()):
                return True
    return False

# --- 세션 상태 초기화 ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "page" not in st.session_state:
    st.session_state.page = "main"

# --- 사이드바 구성 ---
st.sidebar.markdown("### 📂 메뉴")
# 메인 페이지 이동 버튼
if st.sidebar.button("🏠 메인 페이지"):
    st.session_state.page = "main"

# 분석 기능 버튼들
if st.sidebar.button("🎥 영상 분석"):
    st.session_state.page = "video"

if st.sidebar.button("📝 답변 분석"):
    st.session_state.page = "answer"

# 사용자 메뉴 드롭다운
menu_choice = st.sidebar.selectbox("사용자 메뉴", ["선택", "로그인", "회원가입", "로그아웃"] if st.session_state.logged_in else ["선택", "로그인", "회원가입"])

# 메뉴 선택 처리
if menu_choice == "로그인":
    st.session_state.page = "login"
elif menu_choice == "회원가입":
    st.session_state.page = "signup"
elif menu_choice == "로그아웃":
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.success("로그아웃 되었습니다.")
    st.session_state.page = "main"

# --- 페이지 라우팅 ---
if st.session_state.page == "main":
    st.header("🏠 메인 페이지")
    if st.session_state.logged_in:
        st.success(f"{st.session_state.username} 님 환영합니다!")
        st.write("로그인한 사용자만 볼 수 있는 콘텐츠입니다.")

        # 학습정보 섹션 시작
        st.subheader("📘 학습정보")
        st.markdown("### 📊 일자별 종합점수 추이")

        # 예시 데이터 생성
        import pandas as pd
        import plotly.graph_objects as go

        dates = pd.date_range(start='2025-07-01', periods=5, freq='D')  # 시계열 날짜
        scores = [72, 78, 81, 77, 85]
        df = pd.DataFrame({
            '일자': dates,
            '종합점수': scores
        })

        # 그래프 생성
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['일자'],
            y=df['종합점수'],
            mode='lines+markers',
            name='종합점수',
            line=dict(width=3)
        ))
        fig.update_layout(
            xaxis=dict(title='날짜', type='date'),
            yaxis=dict(title='종합점수'),
            height=450,
            margin=dict(t=50, b=50)
        )

        st.plotly_chart(fig, use_container_width=True)
        # ========================
        # 2. 날짜 선택
        # ========================
        st.markdown("---")
        st.markdown("### 📅 일자 선택")
        selected_date = st.selectbox("평가 내용을 확인할 날짜를 선택하세요:", list(evaluation_by_date.keys()))

        # ========================
        # 3. 종합 평가
        # ========================
        data = evaluation_by_date[selected_date]
        st.markdown("### ✅ 종합 평가")
        st.markdown(f"**{data['total']}점 / 100점 만점**")
        st.markdown(data['summary'])

        # ========================
        # 4. 세부 평가
        # ========================
        st.markdown("### 📋 세부 평가 요약")
        detail_df = pd.DataFrame(data['details'], columns=["항목", "점수", "피드백"])
        st.table(detail_df)

        # --- 5. 비언어적 표현 피드백 ---
        st.markdown("### 🗣️ 비언어적 표현 피드백")
        df_nonverbal = pd.DataFrame(data["nonverbal"], columns=["항목", "점수", "피드백"])
        st.table(df_nonverbal)

        # --- 6. 언어적 표현 피드백 ---
        st.markdown("### 🧠 언어적 표현 피드백")
        df_verbal = pd.DataFrame(data["verbal"], columns=["항목", "점수", "피드백"])
        st.table(df_verbal)
    else:
        st.info("로그인 후 더 많은 기능을 이용해보세요!")
elif st.session_state.page == "video":
    st.header("🎥 영상 분석")
    if st.session_state.logged_in:
        tabs = st.tabs(["🎬 영상 분석", "🗂️ 분석 기록"])

        # === 탭 1: 영상 분석 ===
        with tabs[0]:
            with tabs[0]:
                st.subheader("📤 영상 업로드")
                uploaded_video = st.file_uploader("분석할 영상을 업로드하세요", type=["mp4", "mov", "webm"])

                if uploaded_video is not None:
                    st.success("✅ 영상이 성공적으로 업로드되었습니다.")
                    st.video(uploaded_video)
                else:
                    st.info("업로드할 영상 파일을 선택하세요. (지원 형식: mp4, mov, webm)")

        # === 탭 2: 분석 기록 ===
        with tabs[1]:
            st.subheader("📅 최근 분석 기록")

            selected_date = st.selectbox("날짜를 선택하세요:", list(evaluation_by_date.keys()), key="video_date")

            # 선택한 날짜의 비언어 피드백 데이터
            nonverbal_data = evaluation_by_date[selected_date]["nonverbal"]

            # === 1. 분석 영상 표시 ===
            # 같은 날짜의 첫 번째 항목에 있는 영상 URL 사용
            video_url = evaluation_by_date[selected_date].get("nonverbal_video_url")
            if video_url:
                st.video(video_url)

            # === 2. 피드백 표로 정리 ===
            st.markdown("#### 📋 비언어 표현 분석 결과")
            data = evaluation_by_date[selected_date]
            df_nonverbal = pd.DataFrame(data["nonverbal"], columns=["항목", "점수", "피드백"])
            st.table(df_nonverbal)
    else:
        st.info("로그인 후 더 많은 기능을 이용해보세요!")
elif st.session_state.page == "answer":
    st.header("📝 답변 분석")
    if st.session_state.logged_in:
        tabs = st.tabs(["🗣️ 답변 분석", "🗂️ 분석 기록"])

        # === 탭 1: 답변 분석 ===
        with tabs[0]:
            st.subheader("✍️ 답변 입력 및 분석")

            # 질문 프롬프트 (고정 or 랜덤 가능)
            question = "Langchain과 RAG를 사용해보셨던데 Langchain과 RAG에 대해 알고 있는 것을 말씀해주세요."

            # 세션 상태 초기화
            if "chat_submitted" not in st.session_state:
                st.session_state.chat_submitted = False
                st.session_state.chat_answer = ""
            if "follow_up" not in st.session_state:
                st.session_state.follow_up = False

            # 1. AI 질문 출력
            with st.chat_message("assistant"):
                st.markdown(f"**{question}**")

            # 2. 사용자 답변 입력
            if not st.session_state.chat_submitted:
                user_input = st.chat_input("답변을 입력하고 Enter를 눌러주세요")
                if user_input:
                    st.session_state.chat_answer = user_input
                    st.session_state.chat_submitted = True

            # 3. 답변/분석 출력
            if st.session_state.chat_submitted:
                with st.chat_message("user"):
                    st.markdown(st.session_state.chat_answer)

                with st.chat_message("assistant"):
                    st.markdown("### 📊 답변 분석 결과")
                    st.markdown("""
                        - **핵심 논리 명확도**: 85점  
                        - **구조적 표현력**: 80점  
                        - **키워드 활용도**: 78점  
    
                        **💡 피드백 요약**  
                        - 논리적인 구조는 안정적이나 마무리에서 약간 흐름이 약해졌습니다.  
                        - 실무 경험을 연결하면 더 설득력이 높아질 수 있습니다.
                        """)

                # 4. ✅ 추가 질문 생성 버튼 (조건부 표시)
                if not st.session_state.follow_up:
                    if st.button("➕ 추가 질문 생성"):
                        st.session_state.follow_up = True
                        st.success("새로운 질문을 생성했습니다! (예: 다음 질문 출력 예정)")

        # === 탭 2: 분석 기록 ===
        with tabs[1]:
            st.subheader("📅 언어적 표현 분석 기록")

            selected_date = st.selectbox("날짜를 선택하세요:", list(evaluation_by_date.keys()), key="answer_date")

            verbal_data = evaluation_by_date[selected_date]["verbal"]
            df_verbal = pd.DataFrame(verbal_data, columns=["항목", "점수", "피드백"])

            st.markdown(f"#### 📆 선택 날짜: `{selected_date}`")
            st.table(df_verbal)

    else:
        st.info("로그인 후 더 많은 기능을 이용해보세요!")

elif st.session_state.page == "signup":
    st.header("📝 회원가입")
    username = st.text_input("아이디", key="signup_user")
    password = st.text_input("비밀번호", type="password", key="signup_pass")
    if st.button("회원가입"):
        if user_exists(username):
            st.warning("이미 존재하는 아이디입니다.")
        else:
            register_user(username, password)
            st.success("회원가입 완료! 로그인 해주세요.")
            st.session_state.page = "login"

elif st.session_state.page == "login":
    st.header("🔐 로그인")
    username = st.text_input("아이디", key="login_user")
    password = st.text_input("비밀번호", type="password", key="login_pass")
    if st.button("로그인"):
        if login_user(username, password):
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success("로그인 성공!")
            st.session_state.page = "main"
        else:
            st.error("아이디 또는 비밀번호가 틀렸습니다.")
