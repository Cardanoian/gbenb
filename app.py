import os
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import streamlit as st
import google.generativeai as genai
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
from langchain.schema import Document
from langchain.chains import create_retrieval_chain  # 이 줄을 추가합니다.
from langchain.chains.combine_documents import (
    create_stuff_documents_chain,
)  # 이 줄을 추가합니다.

load_dotenv()
# read all pdf files and return text


def get_pdf_text(pdf_docs):
    documents = []
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for i, page in enumerate(pdf_reader.pages):
            text = page.extract_text()
            if text:
                documents.append(
                    Document(
                        page_content=text, metadata={"source": pdf.name, "page": i + 1}
                    )
                )
    return documents


# split text into chunks


def get_text_chunks(documents):  # 인자를 documents로 변경
    splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)
    chunks = splitter.split_documents(documents)  # split_text 대신 split_documents 사용
    return chunks  # list of Document objects


# get embeddings for each chunk


def get_vector_store(chunks):
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001"
    )  # type: ignore
    vector_store = FAISS.from_documents(
        chunks, embedding=embeddings
    )  # from_texts 대신 from_documents 사용
    vector_store.save_local("faiss_index")


def get_conversational_chain():
    prompt_template = """제공된 컨텍스트에서 가능한 한 자세하게 질문에 답변하고, 모든 세부 정보를 제공해야 합니다. 
답변이 제공된 컨텍스트에 없으면 '답변이 컨텍스트에 없습니다'라고만 말하고, 잘못된 답변을 제공하지 마십시오.
컨텍스트:\n {context}\n질문: \n{input}\n\n답변:
"""

    model = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0.3,
    )
    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["context", "input"],  # "question" 대신 "input"으로 변경
    )
    # load_qa_chain 대신 create_stuff_documents_chain 사용
    stuff_documents_chain = create_stuff_documents_chain(model, prompt)
    return stuff_documents_chain  # 변경된 체인 반환


def clear_chat_history():
    st.session_state.messages = [
        {"role": "assistant", "content": "PDF를 업로드하고 질문해주세요."}
    ]


def user_input(user_question):
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001"
    )  # type: ignore

    new_db = FAISS.load_local(
        "faiss_index", embeddings, allow_dangerous_deserialization=True
    )
    retriever = new_db.as_retriever()  # 검색기 생성

    document_chain = get_conversational_chain()  # 문서 체인 가져오기

    # 검색 체인 생성
    retrieval_chain = create_retrieval_chain(retriever, document_chain)

    # invoke 메서드 사용
    response = retrieval_chain.invoke({"input": user_question})

    # 여기에 문서 출처 정보를 추가합니다.
    source_info = []
    # response에서 docs를 가져오는 방식 변경
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
    st.set_page_config(page_title="제미니 PDF 챗봇", page_icon="🤖")

    # Sidebar for uploading PDF files
    with st.sidebar:
        st.title("메뉴:")
        pdf_docs = st.file_uploader(
            "PDF 파일을 업로드하고 '제출 및 처리' 버튼을 클릭하세요",
            accept_multiple_files=True,
        )
        if st.button("제출 및 처리"):
            with st.spinner("처리 중..."):
                documents = get_pdf_text(pdf_docs)  # raw_text 대신 documents로 변경
                text_chunks = get_text_chunks(
                    documents
                )  # raw_text 대신 documents로 변경
                get_vector_store(text_chunks)
                st.success("완료")

    # Main content area for displaying chat messages
    st.title("제미니를 사용하여 PDF 파일과 채팅하기🤖")
    st.write("채팅에 오신 것을 환영합니다!")
    st.sidebar.button("채팅 기록 지우기", on_click=clear_chat_history)

    # Chat input
    # Placeholder for chat messages

    if "messages" not in st.session_state.keys():
        st.session_state.messages = [
            {"role": "assistant", "content": "PDF를 업로드하고 질문해주세요."}
        ]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    if prompt := st.chat_input("여기에 질문을 입력하세요..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

    # Display chat messages and bot response
    if st.session_state.messages[-1]["role"] != "assistant":
        with st.chat_message("assistant"):
            with st.spinner("생각 중..."):
                response_dict = user_input(
                    prompt
                )  # user_input이 딕셔너리를 반환하므로 변수명 변경
                placeholder = st.empty()
                full_response = ""
                for item in response_dict[
                    "output_text"
                ]:  # response_dict에서 output_text를 가져옴
                    full_response += item
                    placeholder.markdown(full_response)
                placeholder.markdown(full_response)
        if response_dict is not None:  # response_dict로 변경
            message = {"role": "assistant", "content": full_response}
            st.session_state.messages.append(message)


if __name__ == "__main__":
    main()
