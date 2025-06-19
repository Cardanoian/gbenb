// src/controllers/DatabaseController.ts
import { DatabaseModel } from '../models/DatabaseModel';
import { ChromaService } from '../services/ChromaService';
import { ChromaDocument } from '../models/types';

export class DatabaseController {
  private databaseModel: DatabaseModel;
  private chromaService: ChromaService;

  constructor(databaseModel: DatabaseModel, chromaService: ChromaService) {
    this.databaseModel = databaseModel;
    this.chromaService = chromaService;
  }

  async initializeDatabase(): Promise<void> {
    try {
      await this.chromaService.initialize();

      const documentCount = await this.chromaService.getDocumentCount();

      this.databaseModel.setConnection({
        isConnected: true,
        documentCount,
      });

      console.log(`Database initialized with ${documentCount} documents`);
    } catch (error) {
      console.error('Database initialization failed:', error);
      this.databaseModel.setConnection({
        isConnected: false,
        documentCount: 0,
      });
      throw error;
    }
  }

  async getDocumentsByCategory(category: string): Promise<ChromaDocument[]> {
    try {
      const documents = await this.chromaService.getDocumentsByCategory(
        category
      );
      return documents;
    } catch (error) {
      console.error('Failed to get documents by category:', error);
      return [];
    }
  }

  async searchSimilarDocuments(
    query: string,
    topK: number = 5
  ): Promise<ChromaDocument[]> {
    try {
      const results = await this.chromaService.similaritySearch(query, topK);
      return results.map((result) => result.document);
    } catch (error) {
      console.error('Similarity search failed:', error);
      return [];
    }
  }

  getDatabaseStatus() {
    return this.databaseModel.getConnection();
  }

  async refreshDatabase(): Promise<void> {
    try {
      await this.initializeDatabase();
    } catch (error) {
      console.error('Database refresh failed:', error);
      throw error;
    }
  }

  // 데이터베이스 통계 정보
  async getDatabaseStats(): Promise<{
    totalDocuments: number;
    categoryCounts: Record<string, number>;
    lastUpdated: Date;
  }> {
    try {
      const connection = this.databaseModel.getConnection();

      // 실제 구현에서는 ChromaDB에서 메타데이터를 통해 카테고리별 통계를 가져와야 함
      const categoryCounts: Record<string, number> = {
        학사관리: 0,
        시설관리: 0,
        급식관리: 0,
        안전관리: 0,
        기타: 0,
      };

      return {
        totalDocuments: connection.documentCount,
        categoryCounts,
        lastUpdated: new Date(),
      };
    } catch (error) {
      console.error('Failed to get database stats:', error);
      return {
        totalDocuments: 0,
        categoryCounts: {},
        lastUpdated: new Date(),
      };
    }
  }
}
