# app.py

import os
import re
import streamlit as st
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
from typing import List, TypedDict, Tuple

from langchain.chains.retrieval import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

load_dotenv()

llm_model = "gemini-2.5-flash"
embedding_model = "text-embedding-3-large"


class ContextDocument(TypedDict):
    source: str
    content: str


class ResponseDict(TypedDict):
    output_text: str
    source_documents: List[ContextDocument]


def get_conversational_chain():
    """개선된 프롬프트 템플릿을 사용하는 체인 생성"""
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

    model = ChatGoogleGenerativeAI(
        model=llm_model,
        temperature=0.3,  # 더 일관된 답변을 위해 낮춤
    )

    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["context", "input"],
    )

    stuff_documents_chain = create_stuff_documents_chain(model, prompt)
    return stuff_documents_chain


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

    # 한글 키워드 확장 (수당 관련)
    keyword_expansions = {
        "담임수당": ["담임수당", "담임 수당", "담임교사 수당", "담임교사수당"],
        "부장수당": ["부장수당", "부장 수당", "부장교사 수당", "부장교사수당"],
        "수당": ["수당", "급여", "보수", "수령"],
        "받을 수 있": ["받을 수 있", "수령 가능", "지급", "받는"],
        "불가": ["불가", "불가능", "받을 수 없", "수령 불가"],
    }

    # 키워드 확장 적용
    expanded_question = question
    for keyword, expansions in keyword_expansions.items():
        if keyword in question:
            expanded_question += f" {' '.join(expansions)}"

    return expanded_question.strip()


def extract_keywords(question: str) -> List[str]:
    """AI를 활용한 키워드 추출 함수 (개선됨)"""

    try:
        # 먼저 AI 기반 키워드 확장 시도
        expanded_keywords = get_expanded_keywords_with_gemini(question)
        if expanded_keywords:
            return expanded_keywords[:8]  # 상위 8개 반환
    except Exception as e:
        print(f"AI 키워드 추출 실패: {e}")

    # 폴백: 기본 키워드 추출
    return extract_basic_keywords(question)


def get_expanded_keywords_with_gemini(question: str) -> List[str]:
    """Gemini AI를 사용한 키워드 확장 함수"""
    try:
        model = ChatGoogleGenerativeAI(
            model=llm_model,
            temperature=0.1,
        )

        prompt = f"""
        다음 질문에서 중요한 키워드들을 추출하고 관련 키워드들로 확장해주세요:
        
        질문: {question}
        
        요구사항:
        1. 핵심 키워드 5-8개를 추출
        2. 각 키워드의 유사어, 동의어, 관련어도 포함
        3. 띄어쓰기 변형도 고려
        4. 쉼표로 구분하여 답변
        
        키워드가 담임수당일 때 출력 예시: 담임 수당, 담임교사 수당, 수당, 급여
        """

        response = model.invoke(prompt)
        keywords = [k.strip() for k in str(response.content).split(",")]
        return keywords[:8]

    except Exception as e:
        print(f"Gemini 키워드 확장 오류: {e}")
        return []


def extract_basic_keywords(question: str) -> List[str]:
    """기본 키워드 추출 함수 (폴백용)"""
    # 불용어 제거
    stopwords = {
        "은",
        "는",
        "이",
        "가",
        "을",
        "를",
        "에",
        "에서",
        "의",
        "로",
        "으로",
        "와",
        "과",
        "하다",
        "있다",
        "없다",
    }

    # 단어 분리 (간단한 방식)
    words = re.findall(r"\b\w+\b", question)
    keywords = [word for word in words if word not in stopwords and len(word) > 1]

    return keywords[:5]


def keyword_text_search(db, question: str) -> List[Tuple]:
    """키워드 기반 텍스트 검색 (벡터 검색의 대안)"""

    keywords = extract_keywords(question)
    if not keywords:
        return []

    # 모든 문서를 가져와서 텍스트 매칭
    try:
        all_docs = db.similarity_search("", k=1000)  # 모든 문서 가져오기

        matching_docs = []
        for doc in all_docs:
            content = doc.page_content.lower()
            question_lower = question.lower()

            # 정확한 매칭 점수 계산
            score = 0
            for keyword in keywords:
                keyword_lower = keyword.lower()
                if keyword_lower in content:
                    # 키워드가 포함된 횟수에 따라 점수 증가
                    count = content.count(keyword_lower)
                    score += count * len(keyword)

            # 원본 질문과의 유사성도 고려
            if any(word in content for word in question_lower.split()):
                score += 10

            if score > 0:
                # 점수를 유사도처럼 변환 (높을수록 좋음)
                similarity_score = min(0.95, score / 100)
                matching_docs.append(
                    (doc, 1 - similarity_score)
                )  # FAISS는 거리 기반이므로 역변환

        # 점수순 정렬
        matching_docs.sort(key=lambda x: x[1])

        return matching_docs

    except Exception as e:
        print(f"키워드 검색 중 오류: {e}")
        return []


def analyze_search_results(
    user_question: str, similar_docs: List[Tuple], threshold: float = 0.7
):
    """검색 결과를 분석하여 관련성을 평가하는 함수"""

    if st.session_state.get("debug_mode", False):
        st.write(f"**검색 분석 결과**")
        st.write(f"질문: {user_question}")
        st.write(f"검색된 문서 수: {len(similar_docs)}")

        relevant_docs = []
        for i, (doc, score) in enumerate(similar_docs):
            with st.expander(f"문서 {i+1} (점수: {score:.3f})"):
                st.write(f"**출처:** {doc.metadata.get('source', 'Unknown')}")
                st.write(f"**내용 길이:** {len(doc.page_content)}")
                st.write(
                    f"**관련성:** {'높음 ✅' if score >= threshold else '낮음 ❌'}"
                )
                st.write(f"**내용 미리보기:**")
                st.text(
                    doc.page_content[:300] + "..."
                    if len(doc.page_content) > 300
                    else doc.page_content
                )

            if score >= threshold:
                relevant_docs.append((doc, score))

        st.write(f"관련성 높은 문서 수: {len(relevant_docs)}")
        return relevant_docs

    # 디버그 모드가 아닐 때는 콘솔에만 출력
    print(f"\n=== 질문: {user_question} ===")
    print(f"검색된 문서 수: {len(similar_docs)}")

    relevant_docs = []
    for i, (doc, score) in enumerate(similar_docs):
        print(f"\n문서 {i+1}:")
        print(f"  점수: {score:.3f}")
        print(f"  출처: {doc.metadata.get('source', 'Unknown')}")
        print(f"  내용 길이: {len(doc.page_content)}")
        print(f"  내용 미리보기: {doc.page_content[:150]}...")

        if score >= threshold:
            relevant_docs.append((doc, score))
            print("  ✅ 관련성 높음")
        else:
            print("  ❌ 관련성 낮음")

    print(f"\n관련성 높은 문서 수: {len(relevant_docs)}")
    return relevant_docs


def check_vector_db_quality():
    """벡터 DB의 품질을 체크하는 함수"""

    if not os.path.exists("faiss_index"):
        st.error("벡터DB가 존재하지 않습니다.")
        return

    try:
        # embeddings = GoogleGenerativeAIEmbeddings(model=embedding_model)
        embeddings = OpenAIEmbeddings(model=embedding_model)
        db = FAISS.load_local(
            "faiss_index", embeddings, allow_dangerous_deserialization=True
        )

        # 벡터 DB 통계
        total_docs = db.index.ntotal
        st.success(f"벡터DB 로드 성공!")
        st.write(f"**총 문서 수:** {total_docs}")

        # 샘플 문서들 확인
        if total_docs > 0:
            sample_docs = db.similarity_search("", k=min(5, total_docs))
            st.write("**샘플 문서들:**")
            for i, doc in enumerate(sample_docs):
                with st.expander(f"샘플 문서 {i+1}"):
                    st.write(f"**출처:** {doc.metadata.get('source', 'Unknown')}")
                    st.write(f"**길이:** {len(doc.page_content)}")
                    st.write(f"**내용:**")
                    st.text(
                        doc.page_content[:200] + "..."
                        if len(doc.page_content) > 200
                        else doc.page_content
                    )

    except Exception as e:
        st.error(f"벡터DB 체크 중 오류 발생: {e}")


def test_keyword_search(keyword: str):
    """특정 키워드로 검색 테스트"""
    if not os.path.exists("faiss_index"):
        st.error("벡터DB가 존재하지 않습니다.")
        return

    try:
        # embeddings = GoogleGenerativeAIEmbeddings(model=embedding_model)
        embeddings = OpenAIEmbeddings(model=embedding_model)
        db = FAISS.load_local(
            "faiss_index", embeddings, allow_dangerous_deserialization=True
        )

        st.write(f"**'{keyword}' 검색 결과:**")

        # 1. 벡터 검색
        vector_results = db.similarity_search_with_score(keyword, k=5)
        st.write(f"벡터 검색 결과: {len(vector_results)}개")

        for i, (doc, score) in enumerate(vector_results):
            with st.expander(f"벡터 검색 {i+1} (점수: {score:.3f})"):
                st.write(f"**출처:** {doc.metadata.get('source', 'Unknown')}")
                # 키워드가 포함된 부분 하이라이트
                content = doc.page_content
                if keyword in content:
                    highlighted = content.replace(keyword, f"**{keyword}**")
                    st.markdown(highlighted)
                else:
                    st.write(content[:300] + "...")

        # 2. 키워드 텍스트 검색
        text_results = keyword_text_search(db, keyword)
        st.write(f"텍스트 검색 결과: {len(text_results)}개")

        for i, (doc, score) in enumerate(text_results[:5]):
            with st.expander(f"텍스트 검색 {i+1} (점수: {score:.3f})"):
                st.write(f"**출처:** {doc.metadata.get('source', 'Unknown')}")
                content = doc.page_content
                if keyword in content:
                    highlighted = content.replace(keyword, f"**{keyword}**")
                    st.markdown(highlighted)
                else:
                    st.write(content[:300] + "...")

    except Exception as e:
        st.error(f"검색 테스트 중 오류: {e}")


def clear_chat_history():
    """채팅 기록을 지우는 함수"""
    st.session_state.messages = [
        {"role": "assistant", "content": "무엇을 도와드릴까요?"}
    ]


def user_input(user_question: str) -> ResponseDict:
    """개선된 사용자 입력 처리 함수"""
    # embeddings = GoogleGenerativeAIEmbeddings(model=embedding_model)
    embeddings = OpenAIEmbeddings(model=embedding_model)

    if not os.path.exists("faiss_index"):
        st.error("벡터DB가 존재하지 않습니다.")
        return {"output_text": "벡터DB가 존재하지 않습니다.", "source_documents": []}

    try:
        new_db = FAISS.load_local(
            "faiss_index", embeddings, allow_dangerous_deserialization=True
        )

        # 유사도 임계값 가져오기 (사이드바에서 설정)
        similarity_threshold = st.session_state.get(
            "similarity_threshold", 0.5
        )  # 기본값을 0.5로 낮춤

        # 질문 전처리
        # user_question = preprocess_question(user_question)

        # 다중 검색 전략 적용
        search_results = []

        # 1. 원본 질문으로 검색
        original_results = new_db.similarity_search_with_score(user_question, k=5)
        search_results.extend(original_results)

        # 2. 전처리된 질문으로 검색
        if user_question != user_question:
            processed_results = new_db.similarity_search_with_score(user_question, k=5)
            search_results.extend(processed_results)

        # 3. 키워드 추출 검색
        keywords = extract_keywords(user_question)
        for keyword in keywords:
            keyword_results = new_db.similarity_search_with_score(keyword, k=3)
            search_results.extend(keyword_results)

        # 중복 제거 및 점수로 정렬
        unique_results = {}
        for doc, score in search_results:
            doc_id = f"{doc.metadata.get('source', '')}_{hash(doc.page_content)}"
            if doc_id not in unique_results or unique_results[doc_id][1] > score:
                unique_results[doc_id] = (doc, score)

        # 점수순 정렬
        similar_docs = sorted(unique_results.values(), key=lambda x: x[1])[:8]

        # 검색 결과 분석
        relevant_docs = analyze_search_results(
            user_question, similar_docs, similarity_threshold
        )

        # 관련성이 높은 문서가 없으면 키워드 기반 텍스트 검색 시도
        if not relevant_docs:
            text_search_results = keyword_text_search(new_db, user_question)
            if text_search_results:
                st.info("💡 키워드 기반 검색으로 관련 문서를 찾았습니다.")
                relevant_docs = text_search_results[:3]  # 상위 3개만 사용

        # 여전히 관련 문서가 없으면 조기 반환
        if not relevant_docs:
            return {
                "output_text": f"죄송합니다. 제공된 문서에서 '{user_question}'에 대한 관련 정보를 찾을 수 없습니다.\n\n다음을 시도해보세요:\n- 더 구체적인 키워드 사용\n- 다른 표현으로 질문\n- 디버그 모드에서 검색 과정 확인",
                "source_documents": [],
            }

        # retriever 설정 개선
        retriever = new_db.as_retriever(
            search_type="similarity",
            search_kwargs={
                "k": 8,
            },
        )

        # RAG 체인 실행
        document_chain = get_conversational_chain()
        retrieval_chain = create_retrieval_chain(retriever, document_chain)

        response = retrieval_chain.invoke({"input": user_question})

        # 참고 문서 정보 수집
        source_info: List[ContextDocument] = []
        for doc in response["context"]:
            if "source" in doc.metadata:
                source_info.append(
                    {
                        "source": doc.metadata["source"],
                        "content": doc.page_content,
                    }
                )

        response_text: str = response["answer"]

        return {"output_text": response_text, "source_documents": source_info}

    except Exception as e:
        st.error(f"답변 생성 중 오류 발생: {e}")
        return {"output_text": f"오류가 발생했습니다: {e}", "source_documents": []}


def add_debug_sidebar():
    """디버그 모드 사이드바 추가"""
    with st.sidebar:
        st.header("🔧 디버그 모드")

        # 디버그 모드 토글
        debug_mode = st.checkbox("디버그 모드 활성화", key="debug_mode")

        if debug_mode:
            st.write("---")

            # AI 키워드 확장 테스트
            st.write("**🤖 AI 키워드 확장 테스트:**")
            test_question = st.text_input(
                "테스트할 질문 입력", placeholder="예: 담임수당을 받을 수 있나요?"
            )
            if st.button("AI 키워드 확장 테스트") and test_question:
                with st.spinner("AI가 키워드를 분석 중..."):
                    expanded = get_expanded_keywords_with_gemini(test_question)
                    st.write(f"**확장된 키워드:** {', '.join(expanded)}")

            st.write("---")

            # 벡터DB 품질 체크 버튼
            if st.button("벡터DB 품질 체크"):
                check_vector_db_quality()

            # 유사도 임계값 설정
            similarity_threshold = st.slider(
                "유사도 임계값",
                min_value=0.0,
                max_value=1.0,
                value=0.5,  # 기본값을 0.5로 낮춤
                step=0.1,
                key="similarity_threshold",
                help="이 값보다 낮은 유사도의 문서는 관련성이 낮다고 판단됩니다.",
            )

            # 특정 키워드로 직접 검색 테스트
            st.write("**직접 검색 테스트:**")
            test_keyword = st.text_input(
                "테스트할 키워드 입력", placeholder="예: 담임수당"
            )
            if st.button("키워드 검색 테스트") and test_keyword:
                test_keyword_search(test_keyword)

            # 검색 설정
            st.write("**검색 설정:**")
            st.write(f"- 유사도 임계값: {similarity_threshold}")
            st.write(f"- 검색할 문서 수: 8개")
            st.write(f"- 모델 온도: 0.3")
            st.write(f"- AI 키워드 확장: ✅ 활성화")
            st.write(f"- 다중 검색 전략: ✅ 활성화")

        return debug_mode


def main():
    """메인 애플리케이션 함수"""
    st.set_page_config(
        page_title="늘봄학교 운영 도우미 챗봇", page_icon="nb_small.png", layout="wide"
    )

    # 디버그 사이드바 추가
    debug_mode = add_debug_sidebar()

    # 메인 헤더
    col1, col2 = st.columns([1, 8])
    with col1:
        if os.path.exists("nb_small.png"):
            st.image("nb_small.png", use_container_width=True)
    with col2:
        st.markdown(
            """
            <div style="display:flex; align-items:center; height:54px;">
                <span style="font-size:2.2em; font-weight:bold; height:54px;">늘봄학교 운영 도우미 챗봇</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write("문의사항 및 오류보고: 포항원동초등학교 교사 김지원")

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
