import fitz
from langchain.text_splitter import RecursiveCharacterTextSplitter

# from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_openai import OpenAIEmbeddings
import streamlit as st
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv
from langchain.schema import Document
from typing import List
import re

load_dotenv()

embedding_model = "text-embedding-3-large"


def clean_pdf_text(text):
    """PDF 텍스트를 더 정교하게 정리하는 함수"""

    # 1. 페이지 번호, 헤더/푸터 패턴 제거
    text = re.sub(r"\n\s*\d+\s*\n", "\n", text)  # 페이지 번호
    text = re.sub(r"\n\s*-\s*\d+\s*-\s*\n", "\n", text)  # -1- 형태 페이지 번호

    # 2. 불필요한 공백 문자 정리
    text = re.sub(r"\xa0", " ", text)  # non-breaking space
    text = re.sub(r"\u2000-\u200f", " ", text)  # 각종 공백 문자

    # 3. 하이픈으로 연결된 단어 처리 (한글의 경우)
    text = re.sub(r"(\S)-\n(\S)", r"\1\2", text)

    # 4. 문장 끝이 아닌 줄바꿈을 공백으로 치환
    # 한글 문장부호도 고려: ., !, ?, …, 다, 음, 임 등
    text = re.sub(r"(?<![.!?…다음임])\n(?=[가-힣A-Za-z])", " ", text)

    # 5. 여러 줄바꿈을 하나로 통합
    text = re.sub(r"\n{2,}", "\n\n", text)

    # 6. 여러 공백을 하나로 통합
    text = re.sub(r" {2,}", " ", text)

    return text.strip()


def get_pdf_text(pdf_docs) -> List[Document]:
    documents: List[Document] = []
    for pdf in pdf_docs:
        full_text = ""
        pdf.seek(0)  # 파일 포인터를 처음으로 이동
        with fitz.open(stream=pdf.read(), filetype="pdf") as doc:
            for page_num in range(doc.page_count):
                page = doc[page_num]
                full_text += page.get_text()  # type: ignore

        cleaned_text = clean_pdf_text(full_text)
        document = Document(page_content=cleaned_text, metadata={"source": pdf.name})
        documents.append(document)
    return documents


def get_text_chunks(documents: List[Document]) -> List[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        separators=[
            "\n\n",  # 문단 구분
            "\n",  # 줄바꿈
            ".",  # 문장 끝
            "!",  # 느낌표
            "?",  # 물음표
            "다.",  # 한글 문장 끝
            "음.",  # 한글 문장 끝
            "임.",  # 한글 문장 끝
            " ",  # 공백
            "",  # 문자 단위
        ],
        is_separator_regex=False,
    )

    chunks = splitter.split_documents(documents)

    # 너무 짧은 청크는 제거 (50자 미만)
    filtered_chunks = [
        chunk for chunk in chunks if len(chunk.page_content.strip()) >= 50
    ]

    print(f"전체 청크 수: {len(chunks)}")
    print(f"필터링 후 청크 수: {len(filtered_chunks)}")
    print(
        f"청크 크기 - 최대: {max(len(chunk.page_content) for chunk in filtered_chunks)}"
    )
    print(
        f"청크 크기 - 최소: {min(len(chunk.page_content) for chunk in filtered_chunks)}"
    )
    print(
        f"청크 크기 - 평균: {sum(len(chunk.page_content) for chunk in filtered_chunks) // len(filtered_chunks)}"
    )

    return filtered_chunks


# get embeddings for each chunk and save to FAISS
def get_vector_store(chunks):
    try:
        embeddings = OpenAIEmbeddings(model=embedding_model)
        vector_store = None
        batch_size = 100  # 한 번에 처리할 청크 수 (조정 가능)

        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i : i + batch_size]
            print(
                f"Processing batch {i // batch_size + 1}/{(len(chunks) + batch_size - 1) // batch_size} with {len(batch_chunks)} chunks..."
            )
            if vector_store is None:
                vector_store = FAISS.from_documents(batch_chunks, embedding=embeddings)
            else:
                vector_store.add_documents(batch_chunks)

        if vector_store:
            vector_store.save_local("faiss_index")
            st.session_state.faiss_index_created = True
            print("FAISS 벡터DB가 성공적으로 생성 및 저장되었습니다.")
        else:
            st.error("처리할 청크가 없어 FAISS 벡터DB를 생성할 수 없습니다.")
            st.session_state.faiss_index_created = False

    except Exception as e:
        st.error(f"FAISS 벡터DB 생성 및 저장 중 오류 발생: {e}")
        print(f"FAISS 벡터DB 생성 및 저장 중 오류 발생: {e}")
        st.session_state.faiss_index_created = False


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
            print("\n".join(map(lambda x: x.name, pdf_docs)))
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
