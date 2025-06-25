import os
import streamlit as st
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from typing import List, TypedDict

load_dotenv()


class ContextDocument(TypedDict):
    source: str
    page: str
    content: str


class ResponseDict(TypedDict):
    output_text: str
    source_documents: List[ContextDocument]


def get_conversational_chain():
    prompt_template = """당신은 초등학교 돌봄교실, 방과후교실, 늘봄교실 운영에 관한 전문가입니다.
제공된 컨텍스트를 바탕으로 담당 교사들의 질문에 대해 가능한 한 자세하고 정확하게 답변해주세요.
답변은 가독성을 위해 적절한 줄바꿈과 문단 구분을 사용하여 작성해주세요.
답변에 컨텍스트 내의 주요 관련 정보를 포함해야 합니다.

이전 대화:\n{chat_history}\n컨텍스트:\n {context}\n질문:\n{input}\n\n답변:
"""

    model = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.4,
    )
    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["chat_history", "context", "input"],
    )
    stuff_documents_chain = create_stuff_documents_chain(model, prompt)
    return stuff_documents_chain


def clear_chat_history():
    st.session_state.messages = [
        {"role": "assistant", "content": "무엇을 도와드릴까요?"}
    ]


def user_input(messages) -> ResponseDict:
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/text-embedding-004"
    )  # type: ignore

    # FAISS 인덱스가 존재하는지 확인
    if not os.path.exists("faiss_index"):
        st.error("벡터DB가 존재하지 않습니다.")
        return {"output_text": "벡터DB가 존재하지 않습니다.", "source_documents": []}

    new_db = FAISS.load_local(
        "faiss_index", embeddings, allow_dangerous_deserialization=True
    )
    retriever = new_db.as_retriever()

    document_chain = get_conversational_chain()

    # 대화 기록과 마지막 질문 분리
    chat_history = ""
    user_question = ""
    if len(messages) > 5:
        messages = messages[-5:]
    for i, message in enumerate(messages):
        if message["role"] == "user":
            if i == len(messages) - 1:  # 마지막 메시지가 사용자 질문
                user_question = message["content"]
            else:
                chat_history += f"사용자: {message['content']}\n"
        elif message["role"] == "assistant":
            chat_history += f"어시스턴트: {message['content']}\n"

    retrieval_chain = create_retrieval_chain(retriever, document_chain)

    response = retrieval_chain.invoke(
        {"input": user_question, "chat_history": chat_history}
    )

    # 참고 문서 정보: 파일명, 페이지, 본문(context)까지 포함
    source_info: List[ContextDocument] = []
    for doc in response["context"]:
        if "source" in doc.metadata and "page" in doc.metadata:
            source_info.append(
                {
                    "source": doc.metadata["source"],
                    "page": doc.metadata["page"],
                    "content": doc.page_content,
                }
            )

    # 답변 텍스트는 그대로 반환하고, 참고 문서는 별도의 키로 반환
    response_text: str = response["answer"]

    # print(response_text)
    return {"output_text": response_text, "source_documents": source_info}


def main():
    st.set_page_config(page_title="늘봄학교 운영 도우미 챗봇", page_icon="💬")

    st.title("늘봄학교 운영 도우미 챗봇 💬")
    st.write("문의사항 및 오류보고: 포항원동초등학교 교사 김지원")

    st.button("채팅 기록 지우기", on_click=clear_chat_history)

    if "messages" not in st.session_state.keys():
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "무엇을 도와드릴까요?",
            }
        ]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    if prompt := st.chat_input("여기에 질문을 입력하세요..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

    if st.session_state.messages[-1]["role"] != "assistant":
        with st.chat_message("assistant"):
            with st.spinner("생각 중..."):
                response_dict = user_input(st.session_state.messages)
                placeholder = st.empty()
                full_response = ""
                # user_input 함수에서 반환된 딕셔너리의 'output_text' 키를 사용
                if response_dict and "output_text" in response_dict:
                    full_response = response_dict["output_text"]
                    placeholder.markdown(full_response)
                else:
                    full_response = "오류: 응답을 생성할 수 없습니다."
                    placeholder.markdown(full_response)

                # 참고 문서 표시 로직 (expander로 구현)
                if (
                    response_dict
                    and "source_documents" in response_dict
                    and response_dict["source_documents"]
                ):
                    st.markdown("---")  # 구분선 추가
                    st.markdown("**참고 문서:**")
                    for doc in response_dict["source_documents"]:
                        with st.expander(
                            f"{doc.get('source')} (페이지: {doc.get('page')})"
                        ):
                            st.write(doc.get("content"))

        if response_dict is not None:
            # 메시지 저장 시 참고 문서는 제외하고 답변 텍스트만 저장
            message = {"role": "assistant", "content": full_response}
            st.session_state.messages.append(message)


if __name__ == "__main__":
    main()
