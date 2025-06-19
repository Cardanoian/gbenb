// src/services/OpenAIService.ts
import { OpenAI } from 'openai';
import { OpenAIConfig } from '../models/types';

export class OpenAIService {
  private client: OpenAI;
  private config: OpenAIConfig;

  constructor(config: OpenAIConfig) {
    this.config = config;
    this.client = new OpenAI({
      apiKey: config.apiKey,
      dangerouslyAllowBrowser: true, // 브라우저에서 사용하기 위해 필요
    });
  }

  async generateResponse(
    prompt: string,
    context: string,
    systemPrompt?: string
  ): Promise<string> {
    try {
      const messages = [
        {
          role: 'system' as const,
          content: systemPrompt || this.getDefaultSystemPrompt(),
        },
        {
          role: 'user' as const,
          content: `컨텍스트: ${context}\n\n질문: ${prompt}`,
        },
      ];

      const response = await this.client.chat.completions.create({
        model: this.config.model,
        messages,
        temperature: this.config.temperature,
        max_tokens: this.config.maxTokens,
      });

      return (
        response.choices[0]?.message?.content || '답변을 생성할 수 없습니다.'
      );
    } catch (error) {
      console.error('OpenAI API error:', error);
      throw error;
    }
  }

  async createEmbedding(text: string): Promise<number[]> {
    try {
      const response = await this.client.embeddings.create({
        model: 'text-embedding-ada-002',
        input: text,
      });

      return response.data[0].embedding;
    } catch (error) {
      console.error('OpenAI embedding error:', error);
      throw error;
    }
  }

  private getDefaultSystemPrompt(): string {
    return `당신은 늘봄학교 업무 관련 질문에 답하는 전문 AI 어시스턴트입니다.
    
다음 규칙을 따라 답변해주세요:
1. 제공된 컨텍스트를 바탕으로 정확하고 도움이 되는 답변을 제공하세요.
2. 늘봄학교 업무와 관련된 내용에 대해서만 답변하세요.
3. 한국어로 친근하고 전문적인 톤으로 답변하세요.
4. 답변할 수 없는 질문이라면 솔직하게 말씀드리세요.
5. 가능한 한 구체적이고 실용적인 정보를 제공하세요.`;
  }
}
