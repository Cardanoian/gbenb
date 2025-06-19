import os
import sys
from pathlib import Path
import subprocess
from dotenv import load_dotenv


def setup_environment():
    """환경 설정"""
    # .env 파일 로드
    load_dotenv()

    # 필요한 디렉토리 생성
    Path("data").mkdir(exist_ok=True)
    Path("services").mkdir(exist_ok=True)
    Path("models").mkdir(exist_ok=True)
    Path("utils").mkdir(exist_ok=True)

    # __init__.py 파일 생성
    for dir_name in ["services", "models", "utils"]:
        init_file = Path(dir_name) / "__init__.py"
        if not init_file.exists():
            init_file.touch()

    print("✅ 환경 설정 완료")


def check_dependencies():
    """의존성 확인"""
    try:
        import streamlit
        import chromadb
        import openai

        print("✅ 모든 필수 패키지가 설치되어 있습니다.")
        return True
    except ImportError as e:
        print(f"❌ 필수 패키지가 누락되었습니다: {e}")
        print("다음 명령어로 설치해주세요: pip install -r requirements.txt")
        return False


def check_api_key():
    """API 키 확인"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your_openai_api_key_here":
        print("❌ OpenAI API 키가 설정되지 않았습니다.")
        print(".env 파일에서 OPENAI_API_KEY를 설정해주세요.")
        return False
    print("✅ OpenAI API 키가 설정되어 있습니다.")
    return True


def run_app():
    """Streamlit 앱 실행"""
    print("🚀 늘봄학교 챗봇을 시작합니다...")

    # Streamlit 실행
    subprocess.run(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            "main.py",
            "--server.address",
            "localhost",
            "--server.port",
            "8501",
            "--theme.base",
            "light",
            "--theme.primaryColor",
            "#667eea",
            "--theme.backgroundColor",
            "#f8f9fa",
            "--theme.secondaryBackgroundColor",
            "#ffffff",
        ]
    )


if __name__ == "__main__":
    print("🌸 늘봄학교 업무 도우미 설정 중...")

    # 환경 설정
    setup_environment()

    # 의존성 확인
    if not check_dependencies():
        sys.exit(1)

    # API 키 확인
    if not check_api_key():
        sys.exit(1)

    # 앱 실행
    run_app()
