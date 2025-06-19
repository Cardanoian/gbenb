// src/services/ChromaService.ts
import { ChromaApi, ChromaClient } from 'chromadb';
import { ChromaDocument, SimilaritySearchResult } from '../models/types';

export class ChromaService {
  private client: ChromaApi;
  private collection: any;
  private collectionName: string;

  constructor(collectionName: string = 'neulbom_documents') {
    this.collectionName = collectionName;
    this.client = new ChromaClient({
      path: '/data/chroma.sqlite3', // 데이터베이스 파일 경로
    });
  }

  async initialize(): Promise<void> {
    try {
      this.collection = await this.client.getCollection({
        name: this.collectionName,
      });
      console.log('ChromaDB collection connected successfully');
    } catch (error) {
      console.error('Failed to connect to ChromaDB:', error);
      throw error;
    }
  }

  async similaritySearch(
    query: string,
    topK: number = 5,
    filter?: Record<string, any>
  ): Promise<SimilaritySearchResult[]> {
    try {
      if (!this.collection) {
        await this.initialize();
      }

      const results = await this.collection.query({
        queryTexts: [query],
        nResults: topK,
        where: filter,
      });

      return this.formatResults(results);
    } catch (error) {
      console.error('Similarity search failed:', error);
      throw error;
    }
  }

  private formatResults(results: any): SimilaritySearchResult[] {
    const documents = results.documents[0] || [];
    const distances = results.distances[0] || [];
    const metadatas = results.metadatas[0] || [];
    const ids = results.ids[0] || [];

    return documents.map((doc: string, index: number) => ({
      document: {
        id: ids[index] || `doc_${index}`,
        content: doc,
        metadata: metadatas[index] || {},
      },
      score: distances[index] !== undefined ? 1 - distances[index] : 0,
    }));
  }

  async getDocumentCount(): Promise<number> {
    try {
      if (!this.collection) {
        await this.initialize();
      }
      const count = await this.collection.count();
      return count;
    } catch (error) {
      console.error('Failed to get document count:', error);
      return 0;
    }
  }

  async getDocumentsByCategory(category: string): Promise<ChromaDocument[]> {
    try {
      const results = await this.collection.query({
        queryTexts: [''],
        nResults: 1000,
        where: { category: category },
      });

      return this.formatResults(results).map((result) => result.document);
    } catch (error) {
      console.error('Failed to get documents by category:', error);
      return [];
    }
  }
}
