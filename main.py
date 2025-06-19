import streamlit as st
import os
from datetime import datetime
import uuid
from typing import List, Dict, Any
from dataclasses import dataclass
from pathlib import Path

# 로컬 모듈 import
from services.chroma_service import ChromaService
from services.openai_service import OpenAIService
from services.langchain_service import LangChainService
from models.chat_models import ChatMessage, ChatSession
from utils.ui_helpers import apply_custom_css, render_message_bubble

# 페이지 설정
st.set_page_config(
    page_title="늘봄학교 업무 도우미",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 커스텀 CSS 적용
apply_custom_css()


def initialize_services():
    """서비스 초기화 - 기존 ChromaDB 파일 우선 로드"""
    if "services_initialized" not in st.session_state:
        try:
            from dotenv import load_dotenv

            load_dotenv()

            data_path = "./data"
            data_dir = Path(data_path)

            if not data_dir.exists():
                st.error("❌ 데이터 디렉토리가 없습니다.")
                st.session_state.services_initialized = False
                st.session_state.database_status = "no_directory"
                return

            # ChromaDB 서비스 초기화 (기존 파일 자동 로드)
            with st.spinner("🔍 기존 ChromaDB 파일을 찾고 있습니다..."):
                chroma_service = ChromaService(
                    persist_directory=data_path,
                    collection_name="nb_vector_db",  # 기본값, 자동으로 기존 컬렉션 찾음
                )

            collection_info = chroma_service.get_collection_info()
            doc_count = collection_info.get("document_count", 0)

            if doc_count == 0:
                st.warning("⚠️ 데이터베이스가 비어있습니다.")
            else:
                st.success(
                    f"✅ {doc_count}개의 문서가 포함된 기존 데이터베이스를 로드했습니다."
                )

            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key or api_key == "your_openai_api_key_here":
                st.error("❌ OpenAI API 키가 설정되지 않았습니다.")
                st.session_state.services_initialized = False
                st.session_state.database_status = "no_api_key"
                return

            openai_service = OpenAIService(api_key=api_key)
            langchain_service = LangChainService(
                chroma_service=chroma_service, openai_service=openai_service
            )

            st.session_state.chroma_service = chroma_service
            st.session_state.langchain_service = langchain_service
            st.session_state.services_initialized = True
            st.session_state.database_status = "connected"
            st.session_state.collection_info = collection_info

        except Exception as e:
            st.error(f"❌ 서비스 초기화 실패: {str(e)}")
            st.session_state.services_initialized = False
            st.session_state.database_status = "error"
            st.session_state.error_message = str(e)


def initialize_chat_session():
    """채팅 세션 초기화"""
    if "chat_session" not in st.session_state:
        st.session_state.chat_session = ChatSession()
    if "messages" not in st.session_state:
        st.session_state.messages = []


def main():
    """메인 애플리케이션"""
    initialize_services()
    initialize_chat_session()

    render_header()

    if not st.session_state.get("services_initialized", False):
        st.error("서비스를 시작할 수 없습니다. 데이터베이스 또는 API 키를 확인하세요.")
        return

    # 채팅 인터페이스
    render_chat_interface()


def render_header():
    """헤더 렌더링"""
    st.markdown(
        """
    <div class="main-header">
        <div class="header-content">
            <h1>🌸 늘봄학교 업무 도우미</h1>
            <p>늘봄 관련 문서를 활용한 AI 챗봇</p>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_chat_interface():
    """채팅 인터페이스 렌더링"""
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    chat_container = st.container()
    with chat_container:
        if not st.session_state.messages:
            st.markdown(
                """
            <div class="welcome-message">
                <div class="welcome-content">
                    <h3>👋 안녕하세요!</h3>
                    <p>늘봄학교 업무와 관련된 질문을 입력해보세요.</p>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )
        else:
            for message in st.session_state.messages:
                render_message_bubble(message)
    st.markdown("</div>", unsafe_allow_html=True)
    render_input_area()


def render_input_area():
    """메시지 입력 영역 렌더링"""
    st.markdown('<div class="input-container">', unsafe_allow_html=True)
    with st.form(key="chat_form", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])
        with col1:
            user_input = st.text_input(
                label="메시지 입력",
                placeholder="늘봄학교에 대해 궁금한 것을 물어보세요...",
                label_visibility="collapsed",
                key="user_input",
            )
        with col2:
            submit_button = st.form_submit_button(
                label="📤", use_container_width=True, type="primary"
            )
    if submit_button and user_input.strip():
        handle_user_message(user_input.strip())
    st.markdown("</div>", unsafe_allow_html=True)


def handle_user_message(user_input: str):
    """사용자 메시지 처리"""
    try:
        user_message = ChatMessage(
            id=str(uuid.uuid4()),
            content=user_input,
            role="user",
            timestamp=datetime.now(),
        )
        st.session_state.messages.append(user_message)
        with st.spinner("🤔 답변을 생성하고 있습니다..."):
            response = st.session_state.langchain_service.process_query(user_input)
            ai_message = ChatMessage(
                id=str(uuid.uuid4()),
                content=response.get(
                    "answer", "죄송합니다. 답변을 생성할 수 없습니다."
                ),
                role="assistant",
                timestamp=datetime.now(),
                sources=response.get("sources", []),
                confidence=response.get("confidence", 0),
            )
            st.session_state.messages.append(ai_message)
        st.rerun()
    except Exception as e:
        st.error(f"메시지 처리 중 오류가 발생했습니다: {str(e)}")


if __name__ == "__main__":
    main()
