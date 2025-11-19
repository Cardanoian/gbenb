import fitz
import streamlit as st
from dotenv import load_dotenv
from typing import List, Dict, cast
import re
import os
import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings
from google import genai
from google.genai import types

load_dotenv()

embedding_model = "models/gemini-embedding-001"

# Gemini API 클라이언트 초기화
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY 환경 변수가 설정되지 않았습니다.")
client = genai.Client(api_key=api_key)


class GeminiEmbeddingFunction(EmbeddingFunction):
    """Gemini API를 사용하는 ChromaDB EmbeddingFunction"""

    def __init__(self, task_type: str = "retrieval_document"):
        self.task_type = task_type
        self.client = client
        self.model = embedding_model

    def __call__(self, input: Documents) -> Embeddings:
        # Documents는 List[str]이므로 그대로 전달
        response = self.client.models.embed_content(
            model=self.model,
            contents=input,
            config=types.EmbedContentConfig(
                task_type=self.task_type,
            ),
        )
        # 여러 문서에 대한 embeddings를 반환 (List[List[float]])
        if response.embeddings is None:
            return []
        embeddings_list = [
            emb.values for emb in response.embeddings if emb.values is not None
        ]
        return cast(Embeddings, embeddings_list)


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


def get_pdf_text(pdf_docs) -> List[Dict]:
    """PDF 파일에서 텍스트를 추출하고 정리"""
    documents: List[Dict] = []
    for pdf in pdf_docs:
        full_text = ""
        pdf.seek(0)  # 파일 포인터를 처음으로 이동
        pdf_bytes = pdf.read()  # 바이트 데이터를 변수에 저장
        with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
            for page_num in range(doc.page_count):
                page = doc[page_num]
                full_text += page.get_text()  # type: ignore

        cleaned_text = clean_pdf_text(full_text)
        document = {"page_content": cleaned_text, "metadata": {"source": pdf.name}}
        documents.append(document)
    return documents


def split_text(
    text: str, chunk_size: int = 1000, chunk_overlap: int = 200
) -> List[str]:
    """텍스트를 청크로 분할하는 함수 (RecursiveCharacterTextSplitter 로직 구현)"""
    separators = [
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
    ]

    def _split_text_recursive(text: str, separators: List[str]) -> List[str]:
        """재귀적으로 텍스트를 분할"""
        if not text:
            return []

        if not separators:
            return [text]

        separator = separators[0]
        remaining_separators = separators[1:]

        if separator == "":
            # 마지막 구분자: 문자 단위로 분할
            return list(text)

        # 구분자로 분할
        splits = text.split(separator)

        # 각 부분을 재귀적으로 처리
        result = []
        for i, split in enumerate(splits):
            if split:
                sub_splits = _split_text_recursive(split, remaining_separators)
                result.extend(sub_splits)
            # 구분자 추가 (마지막이 아닌 경우)
            if i < len(splits) - 1:
                result.append(separator)

        return result

    # 텍스트를 구분자로 분할
    splits = _split_text_recursive(text, separators)

    # 청크 생성
    chunks = []
    current_chunk = ""

    for split in splits:
        test_chunk = current_chunk + split if current_chunk else split

        if len(test_chunk) <= chunk_size:
            current_chunk = test_chunk
        else:
            if current_chunk:
                chunks.append(current_chunk)
                # overlap 처리
                if chunk_overlap > 0 and len(current_chunk) >= chunk_overlap:
                    current_chunk = current_chunk[-chunk_overlap:] + split
                else:
                    current_chunk = split
            else:
                # 현재 청크가 너무 긴 경우 강제로 분할
                if len(split) > chunk_size:
                    # 큰 청크를 강제로 분할
                    for i in range(0, len(split), chunk_size - chunk_overlap):
                        chunk = split[i : i + chunk_size]
                        if chunk:
                            chunks.append(chunk)
                    current_chunk = ""
                else:
                    current_chunk = split

    if current_chunk:
        chunks.append(current_chunk)

    return [chunk.strip() for chunk in chunks if chunk.strip()]


def get_text_chunks(documents: List[Dict]) -> List[Dict]:
    """문서를 청크로 분할"""
    all_chunks = []

    for doc in documents:
        text = doc["page_content"]
        metadata = doc["metadata"]

        # 텍스트 분할
        text_chunks = split_text(text, chunk_size=1000, chunk_overlap=200)

        # 각 청크를 문서로 변환
        for chunk_text in text_chunks:
            if len(chunk_text.strip()) >= 50:  # 너무 짧은 청크 제거
                chunk_doc = {"page_content": chunk_text, "metadata": metadata.copy()}
                all_chunks.append(chunk_doc)

    print(f"필터링 후 청크 수: {len(all_chunks)}")
    if all_chunks:
        print(
            f"청크 크기 - 최대: {max(len(chunk['page_content']) for chunk in all_chunks)}"
        )
        print(
            f"청크 크기 - 최소: {min(len(chunk['page_content']) for chunk in all_chunks)}"
        )
        print(
            f"청크 크기 - 평균: {sum(len(chunk['page_content']) for chunk in all_chunks) // len(all_chunks)}"
        )

    return all_chunks


def get_vector_store(chunks):
    """청크를 ChromaDB에 저장"""
    try:
        # ChromaDB 클라이언트 생성 (영구 저장소)
        chroma_client = chromadb.PersistentClient(path="chroma_db")

        # 컬렉션 생성 또는 가져오기
        collection_name = "pdf_documents"
        try:
            collection = chroma_client.get_collection(
                name=collection_name,
                embedding_function=GeminiEmbeddingFunction(
                    task_type="retrieval_document"
                ),
            )
            # 기존 컬렉션이 있으면 삭제하고 새로 생성
            chroma_client.delete_collection(name=collection_name)
        except:
            pass

        collection = chroma_client.create_collection(
            name=collection_name,
            embedding_function=GeminiEmbeddingFunction(task_type="retrieval_document"),
        )

        batch_size = 100  # 한 번에 처리할 청크 수

        # 배치로 문서 추가
        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i : i + batch_size]
            print(
                f"Processing batch {i // batch_size + 1}/{(len(chunks) + batch_size - 1) // batch_size} with {len(batch_chunks)} chunks..."
            )

            # 문서, 메타데이터, ID 준비
            documents = [chunk["page_content"] for chunk in batch_chunks]
            metadatas = [chunk["metadata"] for chunk in batch_chunks]
            ids = [f"chunk_{i + j}" for j in range(len(batch_chunks))]

            collection.add(documents=documents, metadatas=metadatas, ids=ids)

        st.session_state.faiss_index_created = True
        print("ChromaDB 벡터DB가 성공적으로 생성 및 저장되었습니다.")

    except Exception as e:
        st.error(f"ChromaDB 벡터DB 생성 및 저장 중 오류 발생: {e}")
        print(f"ChromaDB 벡터DB 생성 및 저장 중 오류 발생: {e}")
        st.session_state.faiss_index_created = False


def main():
    st.set_page_config(page_title="PDF 벡터DB 변환기", page_icon="⬆️")

    st.title("PDF 문서를 벡터DB로 변환하기 ⬆️")
    st.write("PDF 파일을 업로드하여 ChromaDB 벡터DB로 변환하고 로컬에 저장합니다.")

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
            st.success("ChromaDB 벡터DB가 성공적으로 생성 및 저장되었습니다!")
            st.info("이제 채팅 앱에서 이 데이터를 사용할 수 있습니다.")
        else:
            st.warning("PDF 파일을 먼저 업로드해주세요.")


if __name__ == "__main__":
    main()
