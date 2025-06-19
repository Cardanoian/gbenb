import chromadb
from pathlib import Path
import json
import streamlit as st


def validate_and_repair_database(data_path="./data"):
    """데이터베이스 유효성 검사 및 복구"""
    print("🔧 데이터베이스 유효성 검사 및 복구...")

    try:
        client = chromadb.PersistentClient(path=str(Path(data_path)))
        collections = client.list_collections()

        if not collections:
            print("❌ 컬렉션이 없습니다. 새로 생성합니다.")
            create_sample_collection(client)
            return

        for collection in collections:
            print(f"\n📚 컬렉션 검사: {collection.name}")

            # 문서 수 확인
            doc_count = collection.count()
            print(f"   문서 수: {doc_count}")

            if doc_count == 0:
                print("   ⚠️ 빈 컬렉션입니다.")
                continue

            # 샘플 데이터 검사
            try:
                sample = collection.get(limit=5)

                # 문서 내용 확인
                if sample["documents"]:
                    avg_length = sum(len(doc) for doc in sample["documents"]) / len(
                        sample["documents"]
                    )
                    print(f"   평균 문서 길이: {avg_length:.0f}자")

                # 메타데이터 확인
                if sample["metadatas"]:
                    metadata_keys = set()
                    for meta in sample["metadatas"]:
                        if meta:
                            metadata_keys.update(meta.keys())
                    print(f"   메타데이터 키: {list(metadata_keys)}")

                # 임베딩 확인
                if sample.get("embeddings") and sample["embeddings"]:
                    embedding_dim = (
                        len(sample["embeddings"][0])
                        if sample["embeddings"][0] is not None
                        else 0
                    )
                    print(f"   임베딩 차원: {embedding_dim}")

                print(f"   ✅ 컬렉션 '{collection.name}' 정상")

            except Exception as e:
                print(f"   ❌ 컬렉션 '{collection.name}' 오류: {str(e)}")

    except Exception as e:
        print(f"❌ 유효성 검사 실패: {str(e)}")


def create_sample_collection(client):
    """샘플 컬렉션 생성"""
    print("📝 샘플 컬렉션을 생성합니다...")

    collection = client.create_collection("neulbom_documents")

    sample_data = [
        {
            "id": "sample_1",
            "content": "늘봄학교는 초등학생을 위한 방과후 통합돌봄 서비스입니다.",
            "metadata": {"category": "기본정보", "source": "시스템 생성"},
        },
        {
            "id": "sample_2",
            "content": "늘봄학교 운영시간은 오전 7시부터 오후 8시까지입니다.",
            "metadata": {"category": "운영시간", "source": "시스템 생성"},
        },
    ]

    collection.add(
        documents=[item["content"] for item in sample_data],
        metadatas=[item["metadata"] for item in sample_data],
        ids=[item["id"] for item in sample_data],
    )

    print(f"✅ 샘플 컬렉션 생성 완료 ({len(sample_data)}개 문서)")


# 메인 앱의 사이드바에 추가할 데이터베이스 정보 표시
def render_database_status():
    """사이드바에 데이터베이스 상세 정보 표시"""
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
        st.metric("문서 수", collection_info.get("document_count", 0))
        st.metric("컬렉션", collection_info.get("name", "Unknown"))

        # 상태 표시
        status = collection_info.get("status", "unknown")
        if status == "connected":
            st.success("✅ 연결됨")
        else:
            st.error("❌ 오류")

        # 데이터 경로
        with st.expander("📁 데이터 경로"):
            st.code(collection_info.get("data_path", "./data"))

        # 샘플 문서 미리보기
        sample_docs = collection_info.get("sample_documents", [])
        if sample_docs:
            with st.expander("📄 샘플 문서"):
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
    else:
        st.error("데이터베이스 서비스가 초기화되지 않았습니다.")
