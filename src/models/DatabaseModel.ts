import {
  ChromaDocument,
  DatabaseConnection,
  SimilaritySearchResult,
} from './types';

export class DatabaseModel {
  private connection: DatabaseConnection;
  private documents: ChromaDocument[] = [];

  constructor() {
    this.connection = {
      isConnected: false,
      collectionName: 'neulbom_documents',
      documentCount: 0,
    };
  }

  // 연결 상태 관리
  setConnection(connection: Partial<DatabaseConnection>) {
    this.connection = { ...this.connection, ...connection };
  }

  getConnection(): DatabaseConnection {
    return { ...this.connection };
  }

  // 문서 관리
  setDocuments(documents: ChromaDocument[]) {
    this.documents = documents;
    this.connection.documentCount = documents.length;
  }

  getDocuments(): ChromaDocument[] {
    return [...this.documents];
  }

  addDocument(document: ChromaDocument) {
    this.documents.push(document);
    this.connection.documentCount = this.documents.length;
  }

  // 유사도 검색 결과 처리
  processSimilarityResults(results: any[]): SimilaritySearchResult[] {
    return results.map((result, index) => ({
      document: {
        id: result.id || `doc_${index}`,
        content: result.document || result.content || '',
        metadata: result.metadata || {},
      },
      score:
        result.distance !== undefined ? 1 - result.distance : result.score || 0,
    }));
  }

  // 카테고리별 문서 필터링
  getDocumentsByCategory(category: string): ChromaDocument[] {
    return this.documents.filter((doc) => doc.metadata.category === category);
  }

  // 검색어로 문서 필터링
  searchDocuments(query: string): ChromaDocument[] {
    const lowercaseQuery = query.toLowerCase();
    return this.documents.filter(
      (doc) =>
        doc.content.toLowerCase().includes(lowercaseQuery) ||
        Object.values(doc.metadata).some(
          (value) =>
            typeof value === 'string' &&
            value.toLowerCase().includes(lowercaseQuery)
        )
    );
  }
}
