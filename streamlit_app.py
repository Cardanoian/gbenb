# app.py

import os
import re
import streamlit as st
from dotenv import load_dotenv
from typing import List, TypedDict, Tuple
import base64
import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings
from google import genai
from google.genai import types

load_dotenv()

llm_model = "gemini-2.5-flash"
embedding_model = "models/gemini-embedding-001"

# Gemini API 클라이언트 초기화
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY 환경 변수가 설정되지 않았습니다.")
client = genai.Client(api_key=api_key)


def get_image_base64(image_path):
    if not os.path.exists(image_path):
        print(f"Error: Image file not found at {image_path}")
        return ""
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")


class GeminiDocumentEmbeddingFunction(EmbeddingFunction):
    """문서 임베딩용 Gemini EmbeddingFunction (RETRIEVAL_DOCUMENT)"""

    def __init__(self):
        self.client = client
        self.model = embedding_model

    def __call__(self, input: Documents) -> Embeddings:
        response = self.client.models.embed_content(
            model=self.model,
            contents=input,
            config=types.EmbedContentConfig(
                task_type="retrieval_document",
            ),
        )
        return response.embeddings[0].values


class GeminiQueryEmbeddingFunction(EmbeddingFunction):
    """쿼리 임베딩용 Gemini EmbeddingFunction (RETRIEVAL_QUERY)"""

    def __init__(self):
        self.client = client
        self.model = embedding_model

    def __call__(self, input: Documents) -> Embeddings:
        response = self.client.models.embed_content(
            model=self.model,
            contents=input,
            config=types.EmbedContentConfig(
                task_type="retrieval_query",
            ),
        )
        return response.embeddings[0].values


class ContextDocument(TypedDict):
    source: str
    content: str


class ResponseDict(TypedDict):
    output_text: str
    source_documents: List[ContextDocument]


def get_conversational_response(user_question: str, context_docs: List[str]) -> str:
    """컨텍스트와 질문을 바탕으로 답변 생성"""
    prompt_template = """당신은 초등학교 돌봄교실, 방과후교실, 늘봄교실 운영에 관한 전문가입니다.

**중요한 지침:**
1. 제공된 컨텍스트가 질문과 관련이 있는지 먼저 판단하세요.
2. 컨텍스트가 질문과 관련이 없다면 "제공된 문서에서 해당 질문에 대한 정보를 찾을 수 없습니다"라고 답변하세요.
3. 관련 정보가 있다면, 그 정보만을 바탕으로 정확하고 자세하게 답변하세요.
4. 컨텍스트에 없는 내용은 추측하거나 만들어내지 마세요.

제공된 컨텍스트:
{context}

질문: {input}

답변 지침:
- 컨텍스트와 질문의 관련성을 먼저 평가하세요
- 관련 있는 정보만 사용하여 답변하세요
- 답변은 명확하고 구체적으로 작성하세요
- 가독성을 위해 적절한 줄바꿈과 문단을 사용하세요

답변:"""

    # 컨텍스트 결합
    context = "\n\n".join(
        [f"[문서 {i+1}]\n{doc}" for i, doc in enumerate(context_docs)]
    )

    # 프롬프트 생성
    prompt = prompt_template.format(context=context, input=user_question)

    # Gemini API 호출
    response = client.models.generate_content(
        model=llm_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.3,
        ),
    )

    return response.text if response.text else ""


def preprocess_question(question: str) -> str:
    """질문을 전처리하여 검색 정확도를 높이는 함수"""

    # 불필요한 공백 제거
    question = re.sub(r"\s+", " ", question).strip()

    # 질문이 너무 짧으면 그대로 반환
    if len(question) < 5:
        return question

    # 존댓말을 평서문으로 변환하여 검색 정확도 향상
    question = re.sub(r"해\s*주세요", "하는 방법", question)
    question = re.sub(r"알려\s*주세요", "", question)
    question = re.sub(r"가르쳐\s*주세요", "", question)

    return question.strip()


def analyze_search_results(
    user_question: str, similar_docs: List[Tuple], threshold: float = 0.7
):
    """검색 결과를 분석하여 관련성을 평가하는 함수"""

    # ChromaDB는 거리(distance)를 반환하므로, 유사도 점수로 변환
    # 거리가 작을수록 유사도가 높으므로, 1 / (1 + distance)로 변환
    def distance_to_similarity(distance: float) -> float:
        return 1 / (1 + distance)

    if st.session_state.get("debug_mode", False):
        st.write(f"**검색 분석 결과**")
        st.write(f"질문: {user_question}")
        st.write(f"검색된 문서 수: {len(similar_docs)}")

        relevant_docs = []
        for i, (doc_text, metadata, distance) in enumerate(similar_docs):
            similarity = distance_to_similarity(distance)
            with st.expander(f"문서 {i+1} (유사도: {similarity:.3f})"):
                st.write(f"**출처:** {metadata.get('source', 'Unknown')}")
                st.write(f"**내용 길이:** {len(doc_text)}")
                st.write(
                    f"**관련성:** {'높음 ✅' if similarity >= threshold else '낮음 ❌'}"
                )
                st.write(f"**내용 미리보기:**")
                st.text(doc_text[:300] + "..." if len(doc_text) > 300 else doc_text)

            if similarity >= threshold:
                relevant_docs.append((doc_text, metadata, distance))

        st.write(f"관련성 높은 문서 수: {len(relevant_docs)}")
        return relevant_docs

    # 디버그 모드가 아닐 때는 콘솔에만 출력
    print(f"\n=== 질문: {user_question} ===")
    print(f"검색된 문서 수: {len(similar_docs)}")

    relevant_docs = []
    for i, (doc_text, metadata, distance) in enumerate(similar_docs):
        similarity = distance_to_similarity(distance)
        print(f"\n문서 {i+1}:")
        print(f"  유사도: {similarity:.3f} (거리: {distance:.3f})")
        print(f"  출처: {metadata.get('source', 'Unknown')}")
        print(f"  내용 길이: {len(doc_text)}")
        print(f"  내용 미리보기: {doc_text[:150]}...")

        if similarity >= threshold:
            relevant_docs.append((doc_text, metadata, distance))
            print("  ✅ 관련성 높음")
        else:
            print("  ❌ 관련성 낮음")

    print(f"\n관련성 높은 문서 수: {len(relevant_docs)}")
    return relevant_docs


def check_vector_db_quality():
    """벡터 DB의 품질을 체크하는 함수"""

    if not os.path.exists("chroma_db"):
        st.error("벡터DB가 존재하지 않습니다.")
        return

    try:
        chroma_client = chromadb.PersistentClient(path="chroma_db")
        collection_name = "pdf_documents"

        try:
            collection = chroma_client.get_collection(
                name=collection_name,
                embedding_function=GeminiDocumentEmbeddingFunction(),
            )
        except:
            st.error("ChromaDB 컬렉션을 찾을 수 없습니다.")
            return

        # 벡터 DB 통계
        total_docs = collection.count()
        st.success(f"벡터DB 로드 성공!")
        st.write(f"**총 문서 수:** {total_docs}")

        # 샘플 문서들 확인
        if total_docs > 0:
            sample_results = collection.get(limit=min(5, total_docs))
            st.write("**샘플 문서들:**")
            for i, (doc_id, doc_text, metadata) in enumerate(
                zip(
                    sample_results["ids"],
                    sample_results["documents"],
                    sample_results["metadatas"],
                )
            ):
                with st.expander(f"샘플 문서 {i+1}"):
                    st.write(
                        f"**출처:** {metadata.get('source', 'Unknown') if metadata else 'Unknown'}"
                    )
                    st.write(f"**길이:** {len(doc_text)}")
                    st.write(f"**내용:**")
                    st.text(doc_text[:200] + "..." if len(doc_text) > 200 else doc_text)

    except Exception as e:
        st.error(f"벡터DB 체크 중 오류 발생: {e}")


def clear_chat_history():
    """채팅 기록을 지우는 함수"""
    st.session_state.messages = [
        {"role": "assistant", "content": "무엇을 도와드릴까요?"}
    ]


def user_input(user_question: str) -> ResponseDict:
    """개선된 사용자 입력 처리 함수"""
    if not os.path.exists("chroma_db"):
        st.error("벡터DB가 존재하지 않습니다.")
        return {"output_text": "벡터DB가 존재하지 않습니다.", "source_documents": []}

    try:
        # ChromaDB 클라이언트 생성
        chroma_client = chromadb.PersistentClient(path="chroma_db")
        collection_name = "pdf_documents"

        try:
            # 문서 검색용 컬렉션 (RETRIEVAL_DOCUMENT 임베딩 사용)
            doc_collection = chroma_client.get_collection(
                name=collection_name,
                embedding_function=GeminiDocumentEmbeddingFunction(),
            )
        except:
            st.error("ChromaDB 컬렉션을 찾을 수 없습니다.")
            return {
                "output_text": "ChromaDB 컬렉션을 찾을 수 없습니다.",
                "source_documents": [],
            }

        # 쿼리 임베딩 생성 (RETRIEVAL_QUERY 사용)
        query_embedding_func = GeminiQueryEmbeddingFunction()
        # Embeddings는 리스트의 리스트이므로, 첫 번째 문서의 임베딩을 가져옴
        query_embeddings_result = query_embedding_func([user_question])
        # query_embeddings는 리스트의 리스트 형식이어야 함
        query_embedding = (
            query_embeddings_result[0]
            if isinstance(query_embeddings_result[0], list)
            else query_embeddings_result
        )

        # 유사도 임계값 가져오기
        similarity_threshold = st.session_state.get("similarity_threshold", 0.5)

        # ChromaDB에서 유사 문서 검색
        # query_embeddings는 리스트의 리스트 형식이어야 함
        results = doc_collection.query(
            query_embeddings=[query_embedding],
            n_results=8,
        )

        # 검색 결과를 (문서, 메타데이터, 거리) 튜플 리스트로 변환
        similar_docs = []
        if results["documents"] and len(results["documents"][0]) > 0:
            for i in range(len(results["documents"][0])):
                doc_text = results["documents"][0][i]
                metadata = (
                    results["metadatas"][0][i]
                    if results["metadatas"] and results["metadatas"][0]
                    else {}
                )
                distance = (
                    results["distances"][0][i]
                    if results["distances"] and results["distances"][0]
                    else 1.0
                )
                similar_docs.append((doc_text, metadata, distance))

        # 검색 결과 분석
        relevant_docs = analyze_search_results(
            user_question, similar_docs, similarity_threshold
        )

        # 여전히 관련 문서가 없으면 조기 반환
        if not relevant_docs:
            return {
                "output_text": f"죄송합니다. 제공된 문서에서 '{user_question}'에 대한 관련 정보를 찾을 수 없습니다.\n\n다음을 시도해보세요:\n- 더 구체적인 키워드 사용\n- 다른 표현으로 질문\n- 디버그 모드에서 검색 과정 확인",
                "source_documents": [],
            }

        # 관련 문서 추출
        context_docs = [doc_text for doc_text, _, _ in relevant_docs]

        # RAG 응답 생성
        response_text = get_conversational_response(user_question, context_docs)

        # 참고 문서 정보 수집
        source_info: List[ContextDocument] = []
        for doc_text, metadata, _ in relevant_docs:
            if metadata and "source" in metadata:
                source_info.append(
                    {
                        "source": metadata["source"],
                        "content": doc_text,
                    }
                )

        return {"output_text": response_text, "source_documents": source_info}

    except Exception as e:
        st.error(f"답변 생성 중 오류 발생: {e}")
        import traceback

        print(traceback.format_exc())
        return {"output_text": f"오류가 발생했습니다: {e}", "source_documents": []}


def add_debug_sidebar():
    """디버그 모드 사이드바 추가"""
    with st.sidebar:
        st.header("📚 학습된 문서 목록")
        st.markdown(
            """
            - 2024년 교육공무직원 노무관리 길라잡이 사례편
            - 2024년 교육공무직원 노무관리 길라잡이 해설편
            - 2025 경북형 늘봄학교 추진 계획(안내용)
            - 2025 늘봄학교 운영길라잡이(개정판)-초등학교편
            - 2025 늘봄학교 참여 학생 귀가 안전관리 강화 방안(안내용)
            - 2025년 경상북도교육감 소속 교육공무직원(늘봄행정실무사) 채용 공고
            - 2025년 교육공무직원 맞춤형복지제도 운영 계획
            - 2025년 늘봄·방과후학교 자유수강권 지원 요령
            - 2025년 늘봄학교 및 늘봄지원실장(임기제 교육연구사) 배치·운영 관련 Q&A
            - 2025년 초중고 학생 교육비 지원 안내 지침
            - 2025학년도 구미교육지원청 방과후학교(선택형 교육 프로그램) 운영 계획
            - 경상북도교육비특별회계 목적사업비 관리 운용지침
            - 늘봄지원실장(임기제 교육연구사) 급여 관련 처리 사항
        """
        )

    return False  # 디버그 모드 비활성화


def main():
    """메인 애플리케이션 함수"""
    st.set_page_config(
        page_title="늘봄학교 챗봇", page_icon="nb_small.png", layout="wide"
    )

    # 디버그 사이드바 추가
    debug_mode = add_debug_sidebar()

    # 메인 헤더
    image_base64 = get_image_base64("nb_small.png")
    st.markdown(
        f"""
        <div style="display:flex; align-items:center; gap:10px; height:54px;margin-bottom:15px;">
            <img src="data:image/png;base64,{image_base64}" width="80" style="height:auto;"/>
            <span style="font-size:2.2em; font-weight:bold;">늘봄학교 챗봇</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("문의사항: 포항원동초등학교 교사 김지원")

    # 디버그 모드 표시
    if debug_mode:
        st.warning(
            "🔧 디버그 모드가 활성화되어 있습니다. 검색 과정이 상세히 표시됩니다."
        )

    # 채팅 기록 지우기 버튼
    if st.button("채팅 기록 지우기", key="clear_chat"):
        clear_chat_history()
        st.rerun()

    # 채팅 메시지 초기화
    if "messages" not in st.session_state.keys():
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "무엇을 도와드릴까요?",
            }
        ]

    # 채팅 메시지 표시
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # 사용자 입력 처리
    if prompt := st.chat_input("여기에 질문을 입력하세요..."):
        # 사용자 메시지 추가
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        # 어시스턴트 응답 생성
        with st.chat_message("assistant"):
            with st.spinner("답변을 생성하고 있습니다..."):
                # 응답 생성
                response_dict = user_input(prompt)

                # 응답 표시
                if response_dict and "output_text" in response_dict:
                    full_response = response_dict["output_text"]
                    st.markdown(full_response)

                    # 참고 문서 표시
                    if (
                        response_dict.get("source_documents")
                        and len(response_dict["source_documents"]) > 0
                    ):

                        st.markdown("---")
                        st.markdown("**📚 참고 문서:**")

                        # 소스 문서를 파일별로 그룹화
                        source_groups = {}
                        for doc in response_dict["source_documents"]:
                            source = doc.get("source", "Unknown")
                            if source not in source_groups:
                                source_groups[source] = []
                            source_groups[source].append(doc.get("content", ""))

                        # 각 파일별로 expander 생성
                        for source, contents in source_groups.items():
                            with st.expander(f"📄 {source} ({len(contents)}개 섹션)"):
                                for i, content in enumerate(contents, 1):
                                    st.write(f"**섹션 {i}:**")
                                    st.write(content)
                                    if i < len(contents):
                                        st.write("---")

                    # 응답을 세션 상태에 저장
                    st.session_state.messages.append(
                        {"role": "assistant", "content": full_response}
                    )

                else:
                    error_message = "죄송합니다. 응답을 생성할 수 없습니다."
                    st.error(error_message)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": error_message}
                    )


if __name__ == "__main__":
    main()
