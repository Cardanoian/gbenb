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
from utils.ui_helpers import apply_custom_css, render_message_bubble, render_sidebar

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
            # 환경 변수 로드
            from dotenv import load_dotenv

            load_dotenv()

            # 데이터 디렉토리 확인
            data_path = "./data"
            data_dir = Path(data_path)

            if not data_dir.exists():
                st.error(f"❌ 데이터 디렉토리가 없습니다: {data_dir.absolute()}")
                st.info(
                    "💡 다음 중 하나를 수행하세요:\n1. `data` 폴더를 생성하고 ChromaDB 파일을 넣으세요\n2. 또는 `python create_sample_data.py`를 실행하세요"
                )
                st.session_state.services_initialized = False
                st.session_state.database_status = "no_directory"
                return

            # ChromaDB 서비스 초기화 (기존 파일 자동 로드)
            with st.spinner("🔍 기존 ChromaDB 파일을 찾고 있습니다..."):
                chroma_service = ChromaService(
                    persist_directory=data_path,
                    collection_name="neulbom_documents",  # 기본값, 자동으로 기존 컬렉션 찾음
                )

            # 컬렉션 정보 확인
            collection_info = chroma_service.get_collection_info()
            doc_count = collection_info.get("document_count", 0)

            if doc_count == 0:
                st.warning("⚠️ 데이터베이스가 비어있습니다.")
                st.info(
                    "💡 Python으로 생성한 ChromaDB 파일을 `data` 폴더에 넣거나, 샘플 데이터를 생성하세요."
                )
            else:
                st.success(
                    f"✅ {doc_count}개의 문서가 포함된 기존 데이터베이스를 로드했습니다."
                )

            # OpenAI 서비스 초기화
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key or api_key == "your_openai_api_key_here":
                st.error("❌ OpenAI API 키가 설정되지 않았습니다.")
                st.info(
                    "💡 `.env` 파일에 `OPENAI_API_KEY=your_actual_key`를 설정하세요."
                )
                st.session_state.services_initialized = False
                st.session_state.database_status = "no_api_key"
                return

            openai_service = OpenAIService(api_key=api_key)

            # LangChain 서비스 초기화
            langchain_service = LangChainService(
                chroma_service=chroma_service, openai_service=openai_service
            )

            # 세션 상태에 저장
            st.session_state.chroma_service = chroma_service
            st.session_state.langchain_service = langchain_service
            st.session_state.services_initialized = True
            st.session_state.database_status = "connected"
            st.session_state.collection_info = collection_info

            # 성공 메시지
            st.success("🎉 모든 서비스가 성공적으로 초기화되었습니다!")

        except Exception as e:
            st.error(f"❌ 서비스 초기화 실패: {str(e)}")
            st.session_state.services_initialized = False
            st.session_state.database_status = "error"
            st.session_state.error_message = str(e)

            # 디버깅 정보 표시
            with st.expander("🔧 디버깅 정보"):
                st.code(f"오류: {str(e)}")
                st.write("**데이터 폴더 상태:**")
                data_dir = Path("./data")
                if data_dir.exists():
                    files = list(data_dir.iterdir())
                    if files:
                        for file in files:
                            st.write(f"- {file.name}")
                    else:
                        st.write("폴더가 비어있음")
                else:
                    st.write("폴더가 존재하지 않음")


def initialize_chat_session():
    """채팅 세션 초기화"""
    if "chat_session" not in st.session_state:
        st.session_state.chat_session = ChatSession()

    if "messages" not in st.session_state:
        st.session_state.messages = []


def main():
    """메인 애플리케이션"""

    # 서비스 초기화
    initialize_services()
    initialize_chat_session()

    # 헤더 섹션
    render_header()

    # 에러 상태별 처리
    if not st.session_state.get("services_initialized", False):
        render_error_state()
        return

    # 메인 레이아웃
    col1, col2 = st.columns([3, 1])

    with col1:
        render_chat_interface()

    with col2:
        render_sidebar()
        render_database_info()


def render_header():
    """헤더 렌더링"""
    st.markdown(
        """
    <div class="main-header">
        <div class="header-content">
            <h1>🌸 늘봄학교 업무 도우미</h1>
            <p>기존 ChromaDB 데이터베이스를 활용한 AI 챗봇</p>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_error_state():
    """에러 상태별 렌더링"""
    error_status = st.session_state.get("database_status", "error")

    if error_status == "no_directory":
        st.markdown(
            """
        <div class="error-container">
            <div class="error-content">
                <div class="error-icon">📁</div>
                <h2>데이터 폴더가 없습니다</h2>
                <p>ChromaDB 파일을 저장할 data 폴더가 필요합니다.</p>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        st.markdown("### 🛠️ 해결 방법:")

        tab1, tab2 = st.tabs(["기존 데이터 사용", "새 데이터 생성"])

        with tab1:
            st.markdown(
                """
            **기존 Python ChromaDB 파일이 있는 경우:**
            
            1. 프로젝트 루트에 `data` 폴더를 생성하세요
            2. 기존 ChromaDB 파일들을 `data` 폴더에 복사하세요
            3. 페이지를 새로고침하세요
            
            ```bash
            mkdir data
            cp /path/to/your/chroma.sqlite3 ./data/
            # 또는 ChromaDB 전체 폴더를 복사
            cp -r /path/to/chromadb/* ./data/
            ```
            """
            )

        with tab2:
            st.markdown(
                """
            **새로운 샘플 데이터를 생성하는 경우:**
            
            ```bash
            python create_sample_data.py
            ```
            """
            )

            if st.button("🚀 샘플 데이터 자동 생성", type="primary"):
                try:
                    # 샘플 데이터 생성 코드 실행
                    from pathlib import Path
                    import chromadb

                    # 데이터 폴더 생성
                    data_dir = Path("./data")
                    data_dir.mkdir(exist_ok=True)

                    # ChromaDB 클라이언트 생성 및 샘플 데이터 추가
                    client = chromadb.PersistentClient(path=str(data_dir))
                    collection = client.create_collection("neulbom_documents")

                    sample_docs = [
                        "늘봄학교는 초등학생을 위한 방과후 통합돌봄 서비스입니다.",
                        "늘봄학교 운영시간은 오전 7시부터 오후 8시까지입니다.",
                        "늘봄학교에서는 학습지도, 특기적성 활동, 돌봄 서비스를 제공합니다.",
                    ]

                    collection.add(
                        documents=sample_docs,
                        ids=[f"doc_{i}" for i in range(len(sample_docs))],
                        metadatas=[{"source": "샘플"} for _ in sample_docs],
                    )

                    st.success("✅ 샘플 데이터가 생성되었습니다!")
                    if st.button("🔄 페이지 새로고침"):
                        st.rerun()

                except Exception as e:
                    st.error(f"❌ 샘플 데이터 생성 실패: {str(e)}")

    elif error_status == "no_api_key":
        st.markdown(
            """
        <div class="error-container">
            <div class="error-content">
                <div class="error-icon">🔑</div>
                <h2>OpenAI API 키가 필요합니다</h2>
                <p>AI 채팅 기능을 사용하기 위해 API 키를 설정해주세요.</p>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
        ### 🛠️ API 키 설정 방법:
        
        1. `.env` 파일을 프로젝트 루트에 생성
        2. 다음 내용을 추가:
        ```
        OPENAI_API_KEY=your_actual_openai_api_key_here
        ```
        3. 페이지를 새로고침
        """
        )

    else:
        st.markdown(
            """
        <div class="error-container">
            <div class="error-content">
                <div class="error-icon">⚠️</div>
                <h2>서비스 초기화 오류</h2>
                <p>시스템을 시작하는 중에 문제가 발생했습니다.</p>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        if "error_message" in st.session_state:
            with st.expander("🔧 상세 오류 정보", expanded=True):
                st.code(st.session_state.error_message)

    if st.button("🔄 다시 시도", key="retry_init"):
        # 세션 상태 초기화 후 재실행
        for key in ["services_initialized", "database_status", "error_message"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()


def render_chat_interface():
    """채팅 인터페이스 렌더링"""
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)

    # 채팅 메시지 표시 영역
    chat_container = st.container()

    with chat_container:
        if not st.session_state.messages:
            # 환영 메시지 (데이터베이스 정보 포함)
            collection_info = st.session_state.get("collection_info", {})
            doc_count = collection_info.get("document_count", 0)
            collection_name = collection_info.get("name", "Unknown")

            st.markdown(
                f"""
            <div class="welcome-message">
                <div class="welcome-content">
                    <h3>👋 안녕하세요!</h3>
                    <p>늘봄학교 업무와 관련된 모든 질문에 답해드립니다.</p>
                    <div class="example-questions">
                        <h4>📊 현재 데이터베이스 정보:</h4>
                        <ul>
                            <li>컬렉션: {collection_name}</li>
                            <li>문서 수: {doc_count}개</li>
                            <li>상태: 연결됨 ✅</li>
                        </ul>
                        <h4>💡 이런 질문을 해보세요:</h4>
                        <ul>
                            <li>"늘봄학교 운영 시간이 어떻게 되나요?"</li>
                            <li>"방과후 프로그램에는 어떤 것들이 있나요?"</li>
                            <li>"늘봄학교 신청은 어떻게 하나요?"</li>
                        </ul>
                    </div>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )
        else:
            # 기존 메시지들 표시
            for message in st.session_state.messages:
                render_message_bubble(message)

    st.markdown("</div>", unsafe_allow_html=True)

    # 입력 영역
    render_input_area()


def render_input_area():
    """메시지 입력 영역 렌더링"""
    st.markdown('<div class="input-container">', unsafe_allow_html=True)

    # 입력 폼
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

    # 메시지 처리
    if submit_button and user_input.strip():
        handle_user_message(user_input.strip())

    st.markdown("</div>", unsafe_allow_html=True)


def handle_user_message(user_input: str):
    """사용자 메시지 처리"""
    try:
        # 사용자 메시지 추가
        user_message = ChatMessage(
            id=str(uuid.uuid4()),
            content=user_input,
            role="user",
            timestamp=datetime.now(),
        )
        st.session_state.messages.append(user_message)

        # 로딩 표시
        with st.spinner(
            "🤔 기존 문서에서 관련 정보를 찾고 답변을 생성하고 있습니다..."
        ):
            # LangChain 서비스로 답변 생성
            response = st.session_state.langchain_service.process_query(user_input)

            # AI 응답 메시지 추가
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

        # 페이지 새로고침으로 새 메시지 표시
        st.rerun()

    except Exception as e:
        st.error(f"메시지 처리 중 오류가 발생했습니다: {str(e)}")


def render_database_info():
    """데이터베이스 상세 정보 렌더링"""
    st.markdown(
        """
    <div class="sidebar-section">
        <h3>💾 데이터베이스 정보</h3>
    </div>
    """,
        unsafe_allow_html=True,
    )

    if hasattr(st.session_state, "chroma_service"):
        collection_info = st.session_state.chroma_service.get_collection_info()

        # 기본 정보
        col1, col2 = st.columns(2)
        with col1:
            st.metric("문서 수", collection_info.get("document_count", 0))
        with col2:
            st.metric("컬렉션", collection_info.get("name", "Unknown"))

        # 상태 표시
        status = collection_info.get("status", "unknown")
        if status == "connected":
            st.success("✅ 데이터베이스 연결됨")
        else:
            st.error(f"❌ 오류: {collection_info.get('error', '알 수 없는 오류')}")

        # 데이터 경로
        with st.expander("📁 데이터 경로"):
            st.code(collection_info.get("data_path", "./data"))

        # 샘플 문서 미리보기
        sample_docs = collection_info.get("sample_documents", [])
        if sample_docs:
            with st.expander("📄 문서 미리보기"):
                for i, doc in enumerate(sample_docs, 1):
                    st.text(f"{i}. {doc}")

        # 모든 컬렉션 목록
        collections = st.session_state.chroma_service.list_all_collections()
        if len(collections) > 1:
            with st.expander("📚 모든 컬렉션"):
                current = st.session_state.chroma_service.collection_name
                for col in collections:
                    if col == current:
                        st.write(f"**{col}** ← 현재 사용중")
                    else:
                        st.write(col)

                # 컬렉션 전환 기능
                st.markdown("---")
                selected_collection = st.selectbox(
                    "다른 컬렉션으로 전환:",
                    collections,
                    index=collections.index(current),
                )

                if st.button("🔄 컬렉션 전환", key="switch_collection"):
                    if st.session_state.chroma_service.switch_collection(
                        selected_collection
                    ):
                        st.success(f"컬렉션을 '{selected_collection}'로 전환했습니다.")
                        st.rerun()
                    else:
                        st.error("컬렉션 전환에 실패했습니다.")


if __name__ == "__main__":
    main()
