# 늘봄 챗봇

Gemini PDF 챗봇은 PDF 문서에 대해 학습된 대화형 AI 모델과 채팅할 수 있는 Streamlit 기반 애플리케이션입니다. 챗봇은 업로드된 PDF 파일에서 정보를 추출하고, 제공된 컨텍스트를 바탕으로 사용자 질문에 답변합니다.

## 주요 기능

- **PDF 업로드:** 사용자가 여러 개의 PDF 파일을 업로드할 수 있습니다.
- **텍스트 추출:** 업로드된 PDF 파일에서 텍스트를 추출합니다.
- **대화형 AI:** Gemini 대화형 AI 모델을 사용하여 사용자 질문에 답변합니다.
- **채팅 인터페이스:** 챗봇과 상호작용할 수 있는 채팅 인터페이스를 제공합니다.

## 시작하기

## 로컬 개발

이 프로젝트를 로컬 머신에서 설정하고 실행하려면 아래 지침을 따르세요.

애플리케이션은 <http://localhost:8501> 에서 확인할 수 있습니다.

**참고:** 이 프로젝트는 Python 3.10 이상이 필요합니다.

1.  **의존성 설치:**

```bash
pip install -r requirements.txt
```

2. **Google API 키 설정:**

- Google API 키를 발급받아 `.env` 파일에 설정하세요.

```bash
GOOGLE_API_KEY=your_api_key_here
```

3. **애플리케이션 실행:**

```bash
streamlit run main.py
```

4. **PDF 업로드:**

- 사이드바를 사용해 PDF 파일을 업로드하세요.
- "Submit & Process"를 클릭해 텍스트를 추출하고 임베딩을 생성하세요.

5. **채팅 인터페이스:**

- 메인 인터페이스에서 AI와 채팅하세요.

## 프로젝트 구조

- `main.py`: 메인 애플리케이션 스크립트 (채팅 인터페이스)
- `pdf_converter_app.py`: PDF 문서를 벡터DB로 변환하는 스크립트
- `.env`: 환경 변수를 저장하는 파일
- `requirements.txt`: 앱 실행에 필요한 파이썬 패키지 목록
- `README.md`: 프로젝트 문서

## 의존성

- PyPDF2
- langchain
- langchain-google-genai
- streamlit
- google-generativeai
- python-dotenv
- langchain-community

## 감사의 글

- [Google Gemini](https://ai.google.com/): 언어 모델 제공
- [Streamlit](https://streamlit.io/): 사용자 인터페이스 프레임워크 제공
