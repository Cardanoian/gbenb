import streamlit as st
from datetime import datetime
from typing import List, Dict, Any
from models.chat_models import ChatMessage


def apply_custom_css():
    """커스텀 CSS 스타일 적용"""
    st.markdown(
        """
    <style>
    /* 전역 스타일 */
    html, body {
        height: 100%;
        margin: 0;
        overflow: hidden; /* 전체 스크롤 방지 */
    }
    .stApp {
        height: 100vh; /* 뷰포트 높이에 맞춤 */
        display: flex;
        flex-direction: column; /* 자식 요소를 세로로 정렬 */
    }
    .main {
        padding: 0rem 1rem;
        flex: 1; /* 남은 공간을 모두 차지 */
        overflow: hidden; /* 내부 스크롤을 위해 외부 스크롤 방지 */
        display: flex; /* 내부 컨텐츠를 위한 flex */
        flex-direction: column; /* 내부 컨텐츠 세로 정렬 */
    }
    
    /* 헤더 스타일 */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem 0;
        margin: -1rem -1rem 2rem -1rem;
        border-radius: 0 0 20px 20px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        flex-shrink: 0; /* 높이 고정 */
    }
    
    .header-content {
        text-align: center;
        max-width: 800px;
        margin: 0 auto;
        padding: 0 2rem;
    }
    
    .header-content h1 {
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
        font-weight: 700;
        background: linear-gradient(45deg, #fff, #f0f8ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .header-content p {
        font-size: 1.2rem;
        opacity: 0.9;
        margin: 0;
    }
    
    /* 채팅 컨테이너 */
    .chat-container {
        background: white;
        border-radius: 20px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        padding: 1.5rem;
        margin-bottom: 1rem; /* 입력 영역과의 간격 유지 */
        flex: 1 1 auto; /* 남은 공간을 채우고, 필요시 축소/확장 */
        min-height: 0; /* flex 아이템의 최소 높이 재정의 */
        overflow-y: auto; /* 내용이 넘칠 경우 스크롤 */
    }
    
    /* 메시지 버블 */
    .message-bubble {
        margin-bottom: 1rem;
        display: flex;
        animation: slideIn 0.3s ease-out;
    }
    
    .message-bubble.user {
        justify-content: flex-end;
    }
    
    .message-bubble.assistant {
        justify-content: flex-start;
    }
    
    .message-content {
        max-width: 80%;
        padding: 1rem 1.5rem;
        border-radius: 20px;
        position: relative;
        word-wrap: break-word;
    }
    
    .message-content.user {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-bottom-right-radius: 5px;
    }
    
    .message-content.assistant {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        border-bottom-left-radius: 5px;
    }
    
    .message-timestamp {
        font-size: 0.8rem;
        opacity: 0.7;
        margin-top: 0.5rem;
    }
    
    .message-sources {
        margin-top: 1rem;
        padding: 0.8rem;
        background: rgba(255,255,255,0.2);
        border-radius: 10px;
        font-size: 0.9rem;
    }
    
    /* 환영 메시지 */
    .welcome-message {
        text-align: center;
        padding: 3rem 2rem;
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        border-radius: 20px;
        color: white;
        margin: 2rem 0;
    }
    
    .welcome-content h3 {
        font-size: 1.8rem;
        margin-bottom: 1rem;
        font-weight: 600;
    }
    
    .welcome-content p {
        font-size: 1.1rem;
        margin-bottom: 2rem;
        opacity: 0.9;
    }
    
    .example-questions {
        background: rgba(255,255,255,0.1);
        padding: 1.5rem;
        border-radius: 15px;
        text-align: left;
        max-width: 500px;
        margin: 0 auto;
    }
    
    .example-questions h4 {
        margin-bottom: 1rem;
        color: #fff;
    }
    
    .example-questions ul {
        list-style: none;
        padding: 0;
    }
    
    .example-questions li {
        padding: 0.5rem 0;
        border-bottom: 1px solid rgba(255,255,255,0.2);
    }
    
    .example-questions li:last-child {
        border-bottom: none;
    }
    
    /* 입력 영역 */
    .stForm {
        background: white;
        border-radius: 15px;
        box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        padding: 1rem;
        margin-top: 1rem; /* 채팅 컨테이너와의 간격 유지 */
        flex-shrink: 0; /* 높이 고정 */
    }
    
    /* 사이드바 스타일 */
    .sidebar-section {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 5px 20px rgba(0,0,0,0.1);
    }
    
    .sidebar-section h3 {
        color: #333;
        margin-bottom: 1rem;
        font-size: 1.2rem;
        font-weight: 600;
    }
    
    .status-badge {
        display: inline-block;
        padding: 0.4rem 0.8rem;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 500;
        margin-bottom: 0.5rem;
    }
    
    .status-connected {
        background: linear-gradient(135deg, #4caf50, #45a049);
        color: white;
    }
    
    .status-error {
        background: linear-gradient(135deg, #f44336, #d32f2f);
        color: white;
    }
    
    .stats-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1rem;
        margin-top: 1rem;
    }
    
    .stat-card {
        background: linear-gradient(135deg, #e3f2fd, #bbdefb);
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
    }
    
    .stat-number {
        font-size: 2rem;
        font-weight: bold;
        color: #1976d2;
        display: block;
    }
    
    .stat-label {
        font-size: 0.9rem;
        color: #666;
        margin-top: 0.2rem;
    }
    
    /* 에러 상태 */
    .error-container {
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 400px;
        padding: 2rem;
    }
    
    .error-content {
        text-align: center;
        background: white;
        padding: 3rem;
        border-radius: 20px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        max-width: 500px;
    }
    
    .error-icon {
        font-size: 4rem;
        margin-bottom: 1rem;
    }
    
    .error-content h2 {
        color: #333;
        margin-bottom: 1rem;
        font-size: 1.5rem;
    }
    
    .error-content p {
        color: #666;
        margin-bottom: 2rem;
        font-size: 1.1rem;
    }
    
    /* 애니메이션 */
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    .pulse {
        animation: pulse 2s infinite;
    }
    
    /* 반응형 디자인 */
    @media (max-width: 768px) {
        .header-content h1 {
            font-size: 2rem;
        }
        
        .header-content p {
            font-size: 1rem;
        }
        
        .message-content {
            max-width: 90%;
        }
        
        .stats-grid {
            grid-template-columns: 1fr;
        }
    }
    
    /* Streamlit 기본 스타일 오버라이드 */
    .stTextInput > div > div > input {
        border-radius: 10px;
        border: 2px solid #e0e0e0;
        padding: 0.75rem;
        font-size: 1rem;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
    }
    
    .stButton > button {
        border-radius: 10px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
        color: white;
        font-weight: 600;
        padding: 0.75rem 1.5rem;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
    }
    
    /* 스크롤바 스타일 */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #667eea, #764ba2);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #5a6fd8, #6a4190);
    }
    </style>
    """,
        unsafe_allow_html=True,
    )


def render_message_bubble(message: ChatMessage):
    """메시지 버블 렌더링"""
    # 시간 포맷팅
    time_str = message.timestamp.strftime("%H:%M")

    # 출처 정보 포맷팅
    sources_html = ""
    if message.sources and len(message.sources) > 0 and message.role == "assistant":
        sources_html = "<div class='message-sources'>"
        sources_html += "<strong>📚 참고 자료:</strong><br>"
        import os
        import re

        for i, source in enumerate(message.sources[:3], 1):
            source_name = source.get("metadata", {}).get("source", f"문서 {i}")
            # 파일명(확장자 제거) 추출
            base_name = os.path.basename(source_name)
            file_name: str = os.path.splitext(base_name)[0]
            if "_" in file_name:
                file_name = file_name.split("_")[1].strip()
            # 페이지 정보 추출 (예: p.23)
            page = source.get("metadata", {}).get("page", None)
            # 만약 page 정보가 없고, source_name에 p.숫자 패턴이 있으면 추출
            if not page:
                m = re.search(r"p\.\d+", source_name)
                page = m.group(0) if m else ""
            else:
                page = f"p.{int(page)+1}"
            # 최종 표기: 파일이름 p.23
            if page:
                display = f"{file_name} {page }"
            else:
                display = file_name
            sources_html += f"• {display}<br>"
        sources_html += "</div>"

    # 메시지 HTML 생성
    st.markdown(
        f"""<div class="message-bubble {message.role}">
    <div class="message-content {message.role}">
        {message.content}
        {sources_html if message.role == "assistant" else "<div></div>"}
        <div class="message-timestamp">{time_str}</div>
    </div>
</div>""",
        unsafe_allow_html=True,
    )
