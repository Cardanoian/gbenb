// src/services/LangChainService.ts
import { OpenAIEmbeddings } from '@langchain/openai';
import { ChromaService } from './ChromaService';
import { OpenAIService } from './OpenAIService';
import { ChatResponse, SimilaritySearchResult } from '../models/types';

export class LangChainService {
  private embeddings: OpenAIEmbeddings;
  private chromaService: ChromaService;
  private openaiService: OpenAIService;

  constructor(
    openaiApiKey: string,
    chromaService: ChromaService,
    openaiService: OpenAIService
  ) {
    this.embeddings = new OpenAIEmbeddings({
      openAIApiKey: openaiApiKey,
      modelName: 'text-embedding-ada-002',
    });
    this.chromaService = chromaService;
    this.openaiService = openaiService;
  }

  async processQuery(query: string): Promise<ChatResponse> {
    try {
      // 1. 유사도 검색으로 관련 문서 찾기
      const similarDocs = await this.chromaService.similaritySearch(query, 5);

      // 2. 컨텍스트 생성
      const context = this.buildContext(similarDocs);

      // 3. OpenAI로 답변 생성
      const answer = await this.openaiService.generateResponse(
        query,
        context,
        this.getSystemPrompt()
      );

      // 4. 응답 객체 생성
      return {
        answer,
        sources: similarDocs.map((result) => result.document),
        confidence: this.calculateConfidence(similarDocs),
      };
    } catch (error) {
      console.error('Query processing failed:', error);
      throw error;
    }
  }

  private buildContext(similarDocs: SimilaritySearchResult[]): string {
    if (similarDocs.length === 0) {
      return '관련 문서를 찾을 수 없습니다.';
    }

    return similarDocs
      .map((result, index) => `문서 ${index + 1}: ${result.document.content}`)
      .join('\n\n');
  }

  private calculateConfidence(similarDocs: SimilaritySearchResult[]): number {
    if (similarDocs.length === 0) return 0;

    const avgScore =
      similarDocs.reduce((sum, doc) => sum + doc.score, 0) / similarDocs.length;
    return Math.round(avgScore * 100);
  }

  private getSystemPrompt(): string {
    return `당신은 늘봄학교 업무 전문 AI 어시스턴트입니다.

제공된 문서들을 바탕으로 질문에 답변해주세요:
- 정확하고 도움이 되는 정보를 제공하세요
- 늘봄학교 업무와 관련된 내용만 답변하세요
- 한국어로 친근하고 전문적인 톤으로 답변하세요
- 컨텍스트에 답이 없다면 솔직하게 말씀드리세요
- 답변 마지막에 참고한 문서 정보를 간략히 언급하세요`;
  }
}
