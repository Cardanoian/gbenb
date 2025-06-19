import streamlit as st
from services.chroma_service import ChromaService
from pathlib import Path


def inspect_database(data_path: str = "./data"):
    """데이터베이스 내용 검사"""
    st.markdown("## 🔍 데이터베이스 검사")

    data_dir = Path(data_path)

    # 1. 디렉토리 내용 확인
    st.markdown("### 📁 데이터 폴더 내용")
    if data_dir.exists():
        files = list(data_dir.iterdir())
        if files:
            for file in files:
                file_size = file.stat().st_size if file.is_file() else "폴더"
                st.write(f"- {file.name} ({file_size} bytes)")
        else:
            st.warning("데이터 폴더가 비어있습니다.")
    else:
        st.error("데이터 폴더가 존재하지 않습니다.")

    # 2. ChromaDB 연결 테스트
    st.markdown("### 🔗 ChromaDB 연결 테스트")
    try:
        chroma_service = ChromaService(persist_directory=data_path)
        collection_info = chroma_service.get_collection_info()

        st.success(f"✅ 연결 성공!")
        st.json(collection_info)

        # 3. 컬렉션 목록
        collections = chroma_service.list_all_collections()
        if collections:
            st.markdown("### 📚 사용 가능한 컬렉션")
            for i, col_name in enumerate(collections, 1):
                st.write(f"{i}. {col_name}")

        # 4. 샘플 검색 테스트
        st.markdown("### 🔍 검색 테스트")
        test_query = st.text_input("테스트 검색어를 입력하세요:", "늘봄학교")
        if st.button("검색 테스트"):
            results = chroma_service.similarity_search(test_query, k=3)
            if results:
                st.success(f"검색 결과: {len(results)}개 문서 발견")
                for i, result in enumerate(results, 1):
                    with st.expander(f"문서 {i} (유사도: {result['score']:.2f})"):
                        st.write(result["content"])
                        st.json(result["metadata"])
            else:
                st.warning("검색 결과가 없습니다.")

    except Exception as e:
        st.error(f"❌ 연결 실패: {str(e)}")


# main.py 에 추가할 디버깅 정보
def render_debug_info():
    """디버깅 정보 표시 (사이드바에 추가)"""
    with st.expander("🔧 디버깅 정보"):
        if hasattr(st.session_state, "chroma_service"):
            collection_info = st.session_state.chroma_service.get_collection_info()
            st.json(collection_info)

            # 컬렉션 전환 옵션
            collections = st.session_state.chroma_service.list_all_collections()
            if len(collections) > 1:
                st.markdown("**컬렉션 전환:**")
                selected_collection = st.selectbox(
                    "사용할 컬렉션 선택:",
                    collections,
                    index=collections.index(
                        st.session_state.chroma_service.collection_name
                    ),
                )

                if st.button("컬렉션 전환"):
                    if st.session_state.chroma_service.switch_collection(
                        selected_collection
                    ):
                        st.success(f"컬렉션을 '{selected_collection}'로 전환했습니다.")
                        st.rerun()
        else:
            st.error("ChromaDB 서비스가 초기화되지 않았습니다.")
