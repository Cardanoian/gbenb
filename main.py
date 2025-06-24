import os
import streamlit as st
import google.generativeai as genai
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

load_dotenv()


def get_conversational_chain():
    prompt_template = """당신은 초등학교 돌봄교실, 방과후교실, 늘봄교실 운영에 관한 전문가입니다.
제공된 컨텍스트를 바탕으로 담당 교사들의 질문에 대해 가능한 한 자세하고 정확하게 답변해주세요.
답변은 컨텍스트 내의 모든 관련 세부 정보를 포함해야 합니다.
만약 제공된 컨텍스트에 질문에 대한 답변이 명확하게 없으면, '제공된 정보로는 답변할 수 없습니다.'라고만 말하고, 추측하거나 잘못된 정보를 제공하지 마십시오.
컨텍스트:\n {context}\n질문: \n{input}\n\n답변:
"""

    model = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0.2,
    )
    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["context", "input"],
    )
    stuff_documents_chain = create_stuff_documents_chain(model, prompt)
    return stuff_documents_chain


def clear_chat_history():
    st.session_state.messages = [
        {"role": "assistant", "content": "무엇을 도와드릴까요?"}
    ]


def user_input(user_question):
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001"
    )  # type: ignore

    # FAISS 인덱스가 존재하는지 확인
    if not os.path.exists("faiss_index"):
        st.error("벡터DB가 존재하지 않습니다.")
        return {"output_text": "벡터DB가 존재하지 않습니다."}

    new_db = FAISS.load_local(
        "faiss_index", embeddings, allow_dangerous_deserialization=True
    )
    retriever = new_db.as_retriever()

    document_chain = get_conversational_chain()

    retrieval_chain = create_retrieval_chain(retriever, document_chain)

    response = retrieval_chain.invoke({"input": user_question})

    source_info = []
    for doc in response["context"]:
        if "source" in doc.metadata and "page" in doc.metadata:
            source_info.append(
                f"{doc.metadata['source']} (페이지: {doc.metadata['page']})"
            )

    if source_info:
        unique_sources = sorted(list(set(source_info)))
        response_text = (
            response["answer"] + "\n\n참고 문서: " + "\n".join(unique_sources)
        )
    else:
        response_text = response["answer"]

    print(response_text)
    return {"output_text": response_text}


def main():
    st.set_page_config(page_title="늘봄학교 운영 도우미 챗봇", page_icon="💬")

    st.title("늘봄학교 운영 도우미 챗봇 💬")
    st.write("늘봄학교 운영에 오신 것을 환영합니다!")

    st.button("채팅 기록 지우기", on_click=clear_chat_history)

    if "messages" not in st.session_state.keys():
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "늘봄학교 운영에 대해 무엇이든 질문해주세요!",
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
                response_dict = user_input(prompt)
                placeholder = st.empty()
                full_response = ""
                # user_input 함수에서 반환된 딕셔너리의 'output_text' 키를 사용
                if response_dict and "output_text" in response_dict:
                    for item in response_dict["output_text"]:
                        full_response += item
                        placeholder.markdown(full_response)
                    placeholder.markdown(full_response)
                else:
                    full_response = "오류: 응답을 생성할 수 없습니다."
                    placeholder.markdown(full_response)
        if response_dict is not None:
            message = {"role": "assistant", "content": full_response}
            st.session_state.messages.append(message)


if __name__ == "__main__":
    main()
