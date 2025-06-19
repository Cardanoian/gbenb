import chromadb
from pathlib import Path
import uuid
import os


def create_sample_database():
    """샘플 ChromaDB 데이터 생성"""

    # 데이터 디렉토리 생성
    data_dir = Path("./data")
    data_dir.mkdir(exist_ok=True)

    # ChromaDB 클라이언트 생성
    client = chromadb.PersistentClient(path=str(data_dir))
    collection_name = os.getenv("CHROMA_COLLECTION_NAME")
    if not collection_name:
        collection_name = ""

    # 기존 컬렉션 삭제 (있는 경우)
    try:
        client.delete_collection(collection_name)
    except:
        pass

    # 새 컬렉션 생성
    collection = client.create_collection(collection_name)

    # 확장된 샘플 데이터
    documents = [
        {
            "content": "늘봄학교는 초등학생을 위한 방과후 통합돌봄 서비스입니다. 맞벌이 가정의 돌봄 공백을 해소하고 아이들에게 안전한 돌봄 환경을 제공합니다.",
            "metadata": {
                "category": "기본정보",
                "source": "늘봄학교 소개",
                "keywords": "늘봄학교,돌봄,초등학생",
            },
        },
        {
            "content": "늘봄학교 운영시간은 학기 중 오전 7시부터 오후 8시까지입니다. 방학 중에는 오전 9시부터 오후 6시까지 운영되며, 토요일과 일요일은 휴무입니다.",
            "metadata": {
                "category": "운영시간",
                "source": "운영 지침",
                "keywords": "운영시간,시간표,휴무",
            },
        },
        {
            "content": "늘봄학교에서 제공하는 프로그램: 1) 학습 지도 (숙제, 복습, 예습), 2) 특기적성 활동 (미술, 음악, 체육), 3) 독서 활동, 4) 문화체험 활동",
            "metadata": {
                "category": "프로그램",
                "source": "프로그램 안내",
                "keywords": "프로그램,학습지도,특기적성",
            },
        },
        {
            "content": "늘봄학교 신청 방법: 각 학교별로 신청을 받으며, 학교 홈페이지나 가정통신문을 통해 안내됩니다. 신청 기간은 보통 학기 시작 2주 전입니다.",
            "metadata": {
                "category": "신청방법",
                "source": "입학 안내",
                "keywords": "신청,등록,접수",
            },
        },
        {
            "content": "늘봄학교 급식 및 간식: 영양사가 직접 관리하는 건강한 간식과 저녁식사를 제공합니다. 알레르기 학생을 위한 대체식도 준비됩니다.",
            "metadata": {
                "category": "급식",
                "source": "급식 관리 지침",
                "keywords": "급식,간식,알레르기,영양",
            },
        },
        {
            "content": "늘봄학교 안전관리: CCTV 설치, 출입통제시스템 운영, 안전요원 배치, 응급처치 교육 등을 통해 학생들의 안전을 보장합니다.",
            "metadata": {
                "category": "안전관리",
                "source": "안전 관리 지침",
                "keywords": "안전,CCTV,응급처치",
            },
        },
        {
            "content": "늘봄학교 이용료: 기본 돌봄은 무료이며, 특별 프로그램은 별도 비용이 발생할 수 있습니다. 저소득층 가정에는 추가 지원이 제공됩니다.",
            "metadata": {
                "category": "이용료",
                "source": "비용 안내",
                "keywords": "이용료,비용,무료,지원",
            },
        },
        {
            "content": "늘봄학교 교사 자격: 초등교사 자격증 소지자, 보육교사 자격증 소지자, 또는 관련 경력이 있는 전문인력이 담당합니다.",
            "metadata": {
                "category": "교사정보",
                "source": "인사 관리",
                "keywords": "교사,자격증,경력",
            },
        },
        {
            "content": "늘봄학교 시설: 전용 교실, 급식실, 휴게실, 체육 시설 등을 갖추고 있으며, 학생들이 안전하고 쾌적하게 생활할 수 있도록 시설을 운영합니다.",
            "metadata": {
                "category": "시설정보",
                "source": "시설 관리",
                "keywords": "시설,교실,급식실,체육시설",
            },
        },
        {
            "content": "늘봄학교 문의처: 각 학교 늘봄학교 담당부서나 교육청 늘봄학교 담당부서로 문의하시기 바랍니다. 온라인으로도 문의가 가능합니다.",
            "metadata": {
                "category": "문의처",
                "source": "연락처 안내",
                "keywords": "문의,연락처,담당부서",
            },
        },
    ]

    # 문서 추가
    ids = [str(uuid.uuid4()) for _ in documents]
    contents = [doc["content"] for doc in documents]
    metadatas = [doc["metadata"] for doc in documents]

    collection.add(documents=contents, metadatas=metadatas, ids=ids)

    print(f"✅ {len(documents)}개의 문서가 ChromaDB에 추가되었습니다.")
    print(f"📁 데이터 위치: {data_dir.absolute()}")


if __name__ == "__main__":
    create_sample_database()
