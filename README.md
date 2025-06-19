"""

# 🌸 늘봄학교 업무 도우미

Streamlit과 LangChain을 활용한 현대적인 AI 챗봇 시스템

## ✨ 주요 기능

- 🤖 **AI 기반 질의응답**: OpenAI GPT를 활용한 자연스러운 대화
- 🔍 **벡터 검색**: ChromaDB를 통한 정확한 정보 검색
- 🎨 **현대적인 UI**: 그라디언트와 애니메이션이 적용된 세련된 디자인
- 📊 **실시간 통계**: 시스템 상태와 사용 통계 모니터링
- 🔒 **안전한 운영**: 환경변수를 통한 API 키 관리

## 🚀 빠른 시작

### 1. 설치

```bash
# 저장소 클론
git clone <repository-url>
cd neulbom-chatbot

# 의존성 설치
pip install -r requirements.txt
```

### 2. 환경 설정

`.env` 파일을 생성하고 OpenAI API 키를 설정하세요:

```
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. 샘플 데이터 생성

```bash
python create_sample_data.py
```

### 4. 실행

```bash
python run.py
```

또는

```bash
streamlit run main.py
```

## 📁 프로젝트 구조

```
neulbom-chatbot/
├── main.py                 # 메인 애플리케이션
├── services/              # 서비스 레이어
│   ├── chroma_service.py   # ChromaDB 서비스
│   ├── openai_service.py   # OpenAI API 서비스
│   └── langchain_service.py # LangChain 통합 서비스
├── models/                # 데이터 모델
│   └── chat_models.py     # 채팅 관련 모델
├── utils/                 # 유틸리티
│   └── ui_helpers.py      # UI 헬퍼 함수
├── data/                  # ChromaDB 데이터
├── requirements.txt       # 의존성 목록
├── .env                   # 환경 변수
├── run.py                 # 실행 스크립트
└── create_sample_data.py  # 샘플 데이터 생성
```

## 🎨 UI 특징

- **그라디언트 배경**: 현대적인 느낌의 그라디언트 색상
- **부드러운 애니메이션**: 메시지 등장 시 슬라이드 효과
- **반응형 디자인**: 모바일과 데스크톱 모두 지원
- **신뢰도 표시**: AI 응답의 신뢰도를 시각적으로 표현
- **출처 표시**: 답변의 근거가 된 문서 정보 제공

## 🔧 커스터마이징

### 시스템 프롬프트 수정

`services/langchain_service.py`의 `_get_system_prompt()` 메서드를 수정하세요.

### UI 색상 변경

`utils/ui_helpers.py`의 CSS 스타일을 수정하여 색상을 변경할 수 있습니다.

### 새로운 문서 추가

`create_sample_data.py`를 수정하여 새로운 문서를 추가하세요.

## 📝 라이선스

MIT License

## 👥 기여하기

1. Fork the Project
2. Create your Feature Branch
3. Commit your Changes
4. Push to the Branch
5. Open a Pull Request

---

**늘봄학교 업무 도우미**로 더 효율적인 업무 관리를 경험해보세요! 🌸
"""
