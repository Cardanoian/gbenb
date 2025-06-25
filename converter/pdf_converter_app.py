import fitz  # PyMuPDF
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import streamlit as st
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv
from langchain.schema import Document

load_dotenv()


# read all pdf files and return text
import re


def clean_pdf_text(text):
    # 문장부호가 아닌 줄바꿈은 공백으로 치환
    text = re.sub(r"(?<![.!?…])\n", " ", text)
    # 여러 줄바꿈은 하나로
    text = re.sub(r"\n+", "\n", text)
    # 불필요한 공백 정리
    text = re.sub(r" +", " ", text)
    return text.strip()


def get_pdf_text(pdf_docs):
    documents = []
    for pdf in pdf_docs:
        pdf.seek(0)  # 파일 포인터를 처음으로 이동
        with fitz.open(stream=pdf.read(), filetype="pdf") as doc:
            for i in range(doc.page_count):
                page = doc[i]
                text = page.get_text()  # type: ignore
                if text:
                    documents.append(
                        Document(
                            # page_content=clean_pdf_text(text),
                            page_content=text,
                            metadata={"source": pdf.name, "page": i + 1},
                        )
                    )
    return documents


# split text into chunks
def get_text_chunks(documents):
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = splitter.split_documents(documents)
    print(
        len(chunks),
        max(map(lambda x: len(x.page_content), chunks)),
        min(map(lambda x: len(x.page_content), chunks)),
    )
    # for i, chunk in enumerate(chunks):
    #     print(i, chunk)
    return chunks


# get embeddings for each chunk and save to FAISS
def get_vector_store(chunks):
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/text-embedding-004"
    )  # type: ignore
    vector_store = FAISS.from_documents(chunks, embedding=embeddings)
    vector_store.save_local("faiss_index")
    st.session_state.faiss_index_created = True  # 인덱스 생성 여부 상태 저장


def main():
    st.set_page_config(page_title="PDF 벡터DB 변환기", page_icon="⬆️")

    st.title("PDF 문서를 벡터DB로 변환하기 ⬆️")
    st.write("PDF 파일을 업로드하여 FAISS 벡터DB로 변환하고 로컬에 저장합니다.")

    pdf_docs = st.file_uploader(
        "PDF 파일을 업로드하고 '변환 및 저장' 버튼을 클릭하세요",
        accept_multiple_files=True,
    )
    if st.button("변환 및 저장"):
        if pdf_docs:
            with st.spinner("PDF 텍스트를 읽는 중..."):
                documents = get_pdf_text(pdf_docs)
            with st.spinner("텍스트를 청크로 분할하는 중..."):
                text_chunks = get_text_chunks(documents)
            with st.spinner("벡터DB를 생성 및 저장하는 중..."):
                get_vector_store(text_chunks)
            st.success("FAISS 벡터DB가 성공적으로 생성 및 저장되었습니다!")
            st.info("이제 채팅 앱에서 이 데이터를 사용할 수 있습니다.")
        else:
            st.warning("PDF 파일을 먼저 업로드해주세요.")


if __name__ == "__main__":
    main()
