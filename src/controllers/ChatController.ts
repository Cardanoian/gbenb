// src/controllers/ChatController.ts
import { ChatModel } from '../models/ChatModel';
import { DatabaseModel } from '../models/DatabaseModel';
import { LangChainService } from '../services/LangChainService';
import { ChromaService } from '../services/ChromaService';
import { OpenAIService } from '../services/OpenAIService';
import { ChatResponse } from '../models/types';

export class ChatController {
  private chatModel: ChatModel;
  private databaseModel: DatabaseModel;
  private langChainService: LangChainService;

  constructor(
    chatModel: ChatModel,
    databaseModel: DatabaseModel,
    langChainService: LangChainService
  ) {
    this.chatModel = chatModel;
    this.databaseModel = databaseModel;
    this.langChainService = langChainService;
  }

  async sendMessage(message: string): Promise<void> {
    try {
      // 사용자 메시지 추가
      this.chatModel.addMessage({
        content: message,
        sender: 'user',
      });

      // 로딩 상태 설정
      this.chatModel.setLoading(true);
      this.chatModel.setError(null);

      // 검증
      if (!this.validateMessage(message)) {
        throw new Error(
          '메시지가 올바르지 않습니다. 늘봄학교 업무 관련 질문을 해주세요.'
        );
      }

      // LangChain을 통해 답변 생성
      const response: ChatResponse = await this.langChainService.processQuery(
        message
      );

      // 봇 응답 추가
      this.chatModel.addMessage({
        content: this.formatBotResponse(response),
        sender: 'bot',
      });
    } catch (error) {
      console.error('Chat error:', error);
      this.chatModel.setError(
        error instanceof Error
          ? error.message
          : '오류가 발생했습니다. 다시 시도해주세요.'
      );
    } finally {
      this.chatModel.setLoading(false);
    }
  }

  private validateMessage(message: string): boolean {
    if (!message || message.trim().length === 0) {
      return false;
    }

    if (message.length > 1000) {
      return false;
    }

    // 욕설이나 부적절한 내용 필터링 (간단한 예시)
    const inappropriateWords = ['욕설1', '욕설2']; // 실제로는 더 포괄적인 필터 필요
    const lowerMessage = message.toLowerCase();

    return !inappropriateWords.some((word) => lowerMessage.includes(word));
  }

  private formatBotResponse(response: ChatResponse): string {
    let formattedResponse = response.answer;

    // 신뢰도가 낮은 경우 경고 메시지 추가
    if (response.confidence < 50) {
      formattedResponse +=
        '\n\n⚠️ 이 답변의 신뢰도가 낮습니다. 정확한 정보는 담당자에게 문의해주세요.';
    }

    // 출처 정보 추가
    if (response.sources.length > 0) {
      formattedResponse += '\n\n📚 참고 자료:';
      response.sources.slice(0, 3).forEach((source, index) => {
        const sourceInfo = source.metadata.source || `문서 ${index + 1}`;
        formattedResponse += `\n• ${sourceInfo}`;
      });
    }

    return formattedResponse;
  }

  clearChat(): void {
    this.chatModel.clearMessages();
    this.chatModel.setError(null);
  }

  getChatState() {
    return this.chatModel.getState();
  }

  subscribeToChatUpdates(callback: (state: any) => void) {
    return this.chatModel.subscribe(callback);
  }
}
