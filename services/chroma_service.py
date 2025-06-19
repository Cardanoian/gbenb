import chromadb
from chromadb.config import Settings
from chromadb.api import ClientAPI  # 추가
from typing import List, Dict, Any, Optional
import os
from pathlib import Path
from chromadb.api.models.Collection import Collection


class ChromaService:
    """ChromaDB 서비스 클래스 - 기존 데이터베이스 로드"""

    def __init__(
        self,
        persist_directory: str = "./data",
        collection_name: str = "neulbom_documents",
    ):
        self.persist_directory = Path(persist_directory)
        self.collection_name = collection_name
        self.client: Optional[ClientAPI] = None  # 타입 변경
        self.collection: Optional[Collection] = None
        self._initialize_client()

    def _initialize_client(self):
        """ChromaDB 클라이언트 초기화 - 기존 데이터베이스 우선 로드"""
        try:
            # 데이터 디렉토리 확인
            if not self.persist_directory.exists():
                raise Exception(
                    f"데이터 디렉토리가 존재하지 않습니다: {self.persist_directory}"
                )

            # ChromaDB 파일들 확인
            chroma_files = (
                list(self.persist_directory.glob("*.sqlite3"))
                + list(self.persist_directory.glob("chroma.sqlite3"))
                + list(self.persist_directory.glob("chroma-*"))
            )

            if chroma_files:
                print(
                    f"✅ 기존 ChromaDB 파일들을 발견했습니다: {[f.name for f in chroma_files]}"
                )
            else:
                print("⚠️ ChromaDB 파일을 찾을 수 없습니다. 새로 생성합니다.")

            # ChromaDB 클라이언트 생성 (기존 데이터베이스 로드)
            self.client = chromadb.PersistentClient(path=str(self.persist_directory))

            if self.client is None:
                raise Exception("ChromaDB 클라이언트 초기화 실패")

            # 기존 컬렉션 목록 확인
            existing_collections = self.client.list_collections()
            collection_names = [col.name for col in existing_collections]

            print(f"📋 발견된 컬렉션들: {collection_names}")

            # 지정된 컬렉션 로드 시도
            if self.collection_name in collection_names:
                self.collection = self.client.get_collection(name=self.collection_name)
                if self.collection is None:
                    raise Exception(f"컬렉션 '{self.collection_name}' 로드 실패")
                doc_count = self.collection.count()
                print(
                    f"✅ 기존 컬렉션 '{self.collection_name}'을 로드했습니다. (문서 수: {doc_count})"
                )

            # 컬렉션이 없으면 첫 번째 컬렉션 사용
            elif existing_collections:
                first_collection = existing_collections[0]
                self.collection = first_collection
                if self.collection is None:
                    raise Exception("첫 번째 컬렉션 로드 실패")
                self.collection_name = first_collection.name
                doc_count = self.collection.count()
                print(
                    f"✅ 첫 번째 컬렉션 '{self.collection_name}'을 사용합니다. (문서 수: {doc_count})"
                )

            # 컬렉션이 전혀 없으면 새로 생성
            else:
                print(
                    f"❌ 기존 컬렉션이 없습니다. 새 컬렉션 '{self.collection_name}'을 생성합니다."
                )
                self.collection = self.client.create_collection(
                    name=self.collection_name
                )
                if self.collection is None:
                    raise Exception(f"컬렉션 '{self.collection_name}' 생성 실패")
                self._load_sample_data()

            # 최종 확인
            if self.collection.count() == 0:
                print("⚠️ 컬렉션이 비어있습니다. 샘플 데이터를 추가합니다.")
                self._load_sample_data()

        except Exception as e:
            raise Exception(f"ChromaDB 초기화 실패: {str(e)}")

    def _load_sample_data(self):
        """샘플 데이터 로드 (백업용)"""
        print("📝 샘플 데이터를 추가하고 있습니다...")

        sample_documents = [
            {
                "id": "doc_1",
                "content": "늘봄학교는 초등학생을 대상으로 하는 방과후 통합돌봄 서비스입니다. 오전 7시부터 오후 8시까지 운영되며, 학습지도와 돌봄 서비스를 제공합니다.",
                "metadata": {"category": "기본정보", "source": "늘봄학교 개요"},
            },
            {
                "id": "doc_2",
                "content": "늘봄학교 운영시간은 학기 중 오전 7시부터 오후 8시까지, 방학 중에는 오전 9시부터 오후 6시까지입니다. 토요일과 일요일은 운영하지 않습니다.",
                "metadata": {"category": "운영시간", "source": "운영 지침"},
            },
            {
                "id": "doc_3",
                "content": "늘봄학교에서 제공하는 프로그램으로는 숙제 지도, 독서 활동, 체육 활동, 예술 활동, 특기적성 개발 프로그램 등이 있습니다.",
                "metadata": {"category": "프로그램", "source": "프로그램 안내"},
            },
            {
                "id": "doc_4",
                "content": "늘봄학교 신청은 각 학교별로 진행되며, 학교 홈페이지나 가정통신문을 통해 안내됩니다. 신청 기간은 학기 시작 전 2주간입니다.",
                "metadata": {"category": "신청방법", "source": "신청 안내"},
            },
            {
                "id": "doc_5",
                "content": "늘봄학교에서는 영양사가 관리하는 간식과 석식을 제공합니다. 알레르기가 있는 학생을 위한 대체식도 준비됩니다.",
                "metadata": {"category": "급식", "source": "급식 관리"},
            },
        ]

        try:
            if self.collection is None:
                print(
                    "❌ ChromaDB 컬렉션이 초기화되지 않았습니다. 샘플 데이터를 추가할 수 없습니다."
                )
                return
            # 문서 추가
            self.collection.add(
                documents=[doc["content"] for doc in sample_documents],
                metadatas=[doc["metadata"] for doc in sample_documents],
                ids=[doc["id"] for doc in sample_documents],
            )
            print(f"✅ {len(sample_documents)}개의 샘플 문서를 추가했습니다.")
        except Exception as e:
            print(f"❌ 샘플 데이터 추가 실패: {str(e)}")

    def similarity_search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """유사도 검색"""
        try:
            if self.collection is None:
                print(
                    "❌ ChromaDB 컬렉션이 초기화되지 않았습니다. 유사도 검색을 수행할 수 없습니다."
                )
                return []
            results = self.collection.query(query_texts=[query], n_results=k)

            # 결과 포맷팅
            formatted_results = []
            if (
                results.get("documents")
                and results["documents"]
                and results["documents"][0]
            ):
                for i in range(
                    len(results["documents"][0])
                ):  # results["documents"][0]의 길이를 사용
                    content = results["documents"][0][
                        i
                    ]  # results["documents"][0]에 접근
                    metadata = {}
                    if (
                        results.get("metadatas")
                        and results["metadatas"]
                        and results["metadatas"][0]
                    ):
                        metadata = results["metadatas"][0][
                            i
                        ]  # results["metadatas"][0]에 접근
                    distance = 0.0  # float으로 초기화
                    if (
                        results.get("distances")
                        and results["distances"]
                        and results["distances"][0]
                    ):
                        distance = results["distances"][0][
                            i
                        ]  # results["distances"][0]에 접근

                    formatted_results.append(
                        {
                            "content": content,
                            "metadata": metadata,
                            "distance": distance,
                            "score": (
                                1.0 - distance
                            ),  # 1.0으로 변경하여 float 연산임을 명시
                        }
                    )

            return formatted_results

        except Exception as e:
            print(f"유사도 검색 오류: {str(e)}")
            return []

    def get_collection_info(self) -> Dict[str, Any]:
        """컬렉션 정보 반환"""
        try:
            if self.collection is None:
                return {
                    "name": self.collection_name,
                    "document_count": 0,
                    "status": "error",
                    "error": "ChromaDB 컬렉션이 초기화되지 않았습니다.",
                    "data_path": str(self.persist_directory.absolute()),
                }
            count = self.collection.count()

            # 샘플 문서 몇 개 가져와서 내용 확인
            sample_docs = []
            if count > 0:
                try:
                    sample_results = self.collection.get(limit=3)
                    if sample_results["documents"]:
                        sample_docs = [
                            doc[:100] + "..." if len(doc) > 100 else doc
                            for doc in sample_results["documents"]
                        ]
                except:
                    pass

            return {
                "name": self.collection_name,
                "document_count": count,
                "status": "connected",
                "sample_documents": sample_docs,
                "data_path": str(self.persist_directory.absolute()),
            }
        except Exception as e:
            return {
                "name": self.collection_name,
                "document_count": 0,
                "status": "error",
                "error": str(e),
                "data_path": str(self.persist_directory.absolute()),
            }

    def list_all_collections(self) -> List[str]:
        """모든 컬렉션 목록 반환"""
        try:
            if self.client is None:
                print(
                    "❌ ChromaDB 클라이언트가 초기화되지 않았습니다. 컬렉션 목록을 조회할 수 없습니다."
                )
                return []
            collections = self.client.list_collections()
            return [col.name for col in collections]
        except Exception as e:
            print(f"컬렉션 목록 조회 오류: {str(e)}")
            return []

    def switch_collection(self, collection_name: str) -> bool:
        """다른 컬렉션으로 전환"""
        try:
            if self.client is None:
                print(
                    "❌ ChromaDB 클라이언트가 초기화되지 않았습니다. 컬렉션을 전환할 수 없습니다."
                )
                return False
            self.collection = self.client.get_collection(name=collection_name)
            self.collection_name = collection_name
            print(f"✅ 컬렉션을 '{collection_name}'로 전환했습니다.")
            return True
        except Exception as e:
            print(f"❌ 컬렉션 전환 실패: {str(e)}")
            return False
