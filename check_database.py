import chromadb
from pathlib import Path
import sys


def check_chromadb(data_path="./data"):
    """ChromaDB 파일 확인 및 분석"""
    print("🔍 ChromaDB 데이터베이스 확인 중...")
    print("=" * 50)

    data_dir = Path(data_path)

    # 1. 디렉토리 확인
    print(f"📁 데이터 경로: {data_dir.absolute()}")
    if not data_dir.exists():
        print("❌ 데이터 디렉토리가 존재하지 않습니다.")
        return False

    # 2. 파일 목록 확인
    print("\n📋 디렉토리 내용:")
    files = list(data_dir.iterdir())
    if not files:
        print("❌ 디렉토리가 비어있습니다.")
        return False

    for file in files:
        if file.is_file():
            size_mb = file.stat().st_size / (1024 * 1024)
            print(f"  📄 {file.name} ({size_mb:.2f} MB)")
        else:
            print(f"  📁 {file.name}/")

    # 3. ChromaDB 연결 시도
    print("\n🔗 ChromaDB 연결 시도...")
    try:
        client = chromadb.PersistentClient(path=str(data_dir))
        print("✅ ChromaDB 클라이언트 연결 성공")
    except Exception as e:
        print(f"❌ ChromaDB 연결 실패: {str(e)}")
        return False

    # 4. 컬렉션 목록 확인
    print("\n📚 컬렉션 목록:")
    try:
        collections = client.list_collections()
        if not collections:
            print("❌ 컬렉션이 없습니다.")
            return False

        for i, collection in enumerate(collections, 1):
            doc_count = collection.count()
            print(f"  {i}. {collection.name} ({doc_count}개 문서)")

            # 각 컬렉션의 샘플 데이터 확인
            if doc_count > 0:
                try:
                    sample = collection.get(limit=1)
                    if sample["documents"]:
                        preview = (
                            sample["documents"][0][:100] + "..."
                            if len(sample["documents"][0]) > 100
                            else sample["documents"][0]
                        )
                        print(f"     샘플: {preview}")
                        if sample["metadatas"] and sample["metadatas"][0]:
                            print(f"     메타데이터: {sample['metadatas'][0]}")
                except Exception as e:
                    print(f"     ⚠️ 샘플 데이터 조회 실패: {str(e)}")

    except Exception as e:
        print(f"❌ 컬렉션 조회 실패: {str(e)}")
        return False

    # 5. 권장 컬렉션 선택
    print("\n💡 권장사항:")
    if len(collections) == 1:
        print(f"   단일 컬렉션 '{collections[0].name}'을 사용하세요.")
    else:
        # 가장 많은 문서를 가진 컬렉션 추천
        best_collection = max(collections, key=lambda c: c.count())
        print(
            f"   '{best_collection.name}' 컬렉션을 사용하는 것을 권장합니다. ({best_collection.count()}개 문서)"
        )

    print("\n✅ 데이터베이스 확인 완료!")
    return True


def test_search(data_path="./data", collection_name=None):
    """검색 기능 테스트"""
    print("\n🔍 검색 기능 테스트...")
    print("=" * 50)

    try:
        client = chromadb.PersistentClient(path=str(Path(data_path)))
        collections = client.list_collections()

        if not collections:
            print("❌ 사용 가능한 컬렉션이 없습니다.")
            return

        # 컬렉션 선택
        if collection_name:
            try:
                collection = client.get_collection(collection_name)
            except:
                print(f"❌ 컬렉션 '{collection_name}'을 찾을 수 없습니다.")
                collection = collections[0]
        else:
            collection = collections[0]

        print(f"📚 사용 컬렉션: {collection.name}")

        # 테스트 쿼리들
        test_queries = ["늘봄학교", "운영시간", "신청방법", "프로그램", "급식"]

        for query in test_queries:
            print(f"\n🔍 검색어: '{query}'")
            try:
                results = collection.query(query_texts=[query], n_results=3)

                if (
                    results["documents"]
                    and results["documents"][0] is not None
                    and len(results["documents"][0]) > 0
                    and results["distances"]
                    and results["distances"][0] is not None
                    and len(results["distances"][0]) > 0
                ):
                    print(f"   ✅ {len(results['documents'][0])}개 결과 발견")
                    for i, (doc, distance) in enumerate(
                        zip(results["documents"][0], results["distances"][0])
                    ):
                        similarity = 1 - distance
                        preview = doc[:80] + "..." if len(doc) > 80 else doc
                        print(f"   {i+1}. (유사도: {similarity:.3f}) {preview}")
                else:
                    print("   ❌ 검색 결과 없음")

            except Exception as e:
                print(f"   ❌ 검색 오류: {str(e)}")

    except Exception as e:
        print(f"❌ 검색 테스트 실패: {str(e)}")


if __name__ == "__main__":
    # 명령행 인자 처리
    data_path = sys.argv[1] if len(sys.argv) > 1 else "./data"
    collection_name = sys.argv[2] if len(sys.argv) > 2 else None

    print("🌸 늘봄학교 ChromaDB 데이터베이스 확인 도구")
    print("=" * 50)

    # 기본 확인
    if check_chromadb(data_path):
        # 검색 테스트
        test_search(data_path, collection_name)
    else:
        print("\n❌ 데이터베이스 확인에 실패했습니다.")
        print("\n💡 해결 방법:")
        print("1. 데이터 폴더에 ChromaDB 파일이 있는지 확인")
        print("2. 파일 권한 확인")
        print("3. ChromaDB 버전 호환성 확인")
