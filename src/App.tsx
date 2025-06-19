import { useState, useRef, useEffect } from 'react';
import {
  Send,
  User,
  FileText,
  MessageCircle,
  Sparkles,
  HelpCircle,
  ThumbsUp,
  ThumbsDown,
  Copy,
  X,
  AlertCircle,
  BookOpen,
} from 'lucide-react';

// LangChain imports - 실제 사용 시 이렇게 import
import { OpenAI, OpenAIEmbeddings } from '@langchain/openai';
import { ChatOpenAI } from '@langchain/openai';
import { MemoryVectorStore } from 'langchain/vectorstores/memory';
import { Document } from '@langchain/core/documents';
import { PromptTemplate } from '@langchain/core/prompts';
import { RunnableSequence } from '@langchain/core/runnables';
import { StringOutputParser } from '@langchain/core/output_parsers';
import type { VectorStore } from '@langchain/core/vectorstores';

// 환경변수
const OPENAI_API_KEY = import.meta.env.VITE_OPENAI_API_KEY;

// LangChain 모킹 클래스들 (실제로는 위의 import를 사용)
// class Document {
//   constructor(fields) {
//     this.pageContent = fields.pageContent;
//     this.metadata = fields.metadata || {};
//   }
// }

// class OpenAIEmbeddings {
//   constructor(config) {
//     this.apiKey = config.openAIApiKey;
//     this.modelName = config.modelName || 'text-embedding-3-small';
//   }

//   async embedQuery(text) {
//     const response = await fetch('https://api.openai.com/v1/embeddings', {
//       method: 'POST',
//       headers: {
//         'Content-Type': 'application/json',
//         Authorization: `Bearer ${this.apiKey}`,
//       },
//       body: JSON.stringify({
//         model: this.modelName,
//         input: text,
//       }),
//     });

//     if (!response.ok) {
//       throw new Error(`OpenAI API error: ${response.status}`);
//     }

//     const data = await response.json();
//     return data.data[0].embedding;
//   }

//   async embedDocuments(texts) {
//     const embeddings = [];
//     for (const text of texts) {
//       const embedding = await this.embedQuery(text);
//       embeddings.push(embedding);
//     }
//     return embeddings;
//   }
// }

// class ChatOpenAI {
//   constructor(config) {
//     this.apiKey = config.openAIApiKey;
//     this.modelName = config.modelName || 'gpt-4o-mini';
//     this.temperature = config.temperature || 0.7;
//     this.maxTokens = config.maxTokens || 1000;
//   }

//   async invoke(messages) {
//     const formattedMessages = Array.isArray(messages)
//       ? messages
//       : [{ role: 'user', content: messages }];

//     const response = await fetch('https://api.openai.com/v1/chat/completions', {
//       method: 'POST',
//       headers: {
//         'Content-Type': 'application/json',
//         Authorization: `Bearer ${this.apiKey}`,
//       },
//       body: JSON.stringify({
//         model: this.modelName,
//         messages: formattedMessages,
//         max_tokens: this.maxTokens,
//         temperature: this.temperature,
//       }),
//     });

//     if (!response.ok) {
//       throw new Error(`OpenAI API error: ${response.status}`);
//     }

//     const data = await response.json();
//     return {
//       content: data.choices[0].message.content.trim(),
//     };
//   }
// }

// class MemoryVectorStore {
//   constructor(embeddings, config = {}) {
//     this.embeddings = embeddings;
//     this.documents = [];
//     this.vectors = [];
//   }

//   static async fromDocuments(documents, embeddings) {
//     const vectorStore = new MemoryVectorStore(embeddings);
//     await vectorStore.addDocuments(documents);
//     return vectorStore;
//   }

//   async addDocuments(documents) {
//     const texts = documents.map((doc) => doc.pageContent);
//     const vectors = await this.embeddings.embedDocuments(texts);

//     this.documents.push(...documents);
//     this.vectors.push(...vectors);
//   }

//   async similaritySearch(query, k = 4) {
//     const queryVector = await this.embeddings.embedQuery(query);
//     const similarities = this.vectors.map((vector, index) => ({
//       document: this.documents[index],
//       similarity: this.cosineSimilarity(queryVector, vector),
//       index,
//     }));

//     return similarities
//       .sort((a, b) => b.similarity - a.similarity)
//       .slice(0, k)
//       .map((item) => item.document);
//   }

//   cosineSimilarity(vecA, vecB) {
//     const dotProduct = vecA.reduce((sum, a, i) => sum + a * vecB[i], 0);
//     const magnitudeA = Math.sqrt(vecA.reduce((sum, a) => sum + a * a, 0));
//     const magnitudeB = Math.sqrt(vecB.reduce((sum, a) => sum + a * a, 0));
//     return dotProduct / (magnitudeA * magnitudeB);
//   }
// }

// class PromptTemplate {
//   constructor(config) {
//     this.template = config.template;
//     this.inputVariables = config.inputVariables;
//   }

//   static fromTemplate(template) {
//     const inputVariables = [...template.matchAll(/\{(\w+)\}/g)].map(
//       (match) => match[1]
//     );
//     return new PromptTemplate({ template, inputVariables });
//   }

//   format(values) {
//     let formatted = this.template;
//     for (const [key, value] of Object.entries(values)) {
//       formatted = formatted.replace(new RegExp(`\\{${key}\\}`, 'g'), value);
//     }
//     return formatted;
//   }

//   pipe(nextRunnable) {
//     return new RunnableSequence([this, nextRunnable]);
//   }
// }

// class StringOutputParser {
//   parse(text) {
//     return typeof text === 'string' ? text : text.content;
//   }

//   pipe(nextRunnable) {
//     return new RunnableSequence([this, nextRunnable]);
//   }
// }

// class RunnableSequence {
//   constructor(steps) {
//     this.steps = steps;
//   }

//   async invoke(input) {
//     let result = input;
//     for (const step of this.steps) {
//       if (step instanceof PromptTemplate) {
//         result = step.format(result);
//       } else if (step instanceof ChatOpenAI) {
//         result = await step.invoke(result);
//       } else if (step instanceof StringOutputParser) {
//         result = step.parse(result);
//       } else if (typeof step.invoke === 'function') {
//         result = await step.invoke(result);
//       }
//     }
//     return result;
//   }

//   pipe(nextRunnable) {
//     return new RunnableSequence([...this.steps, nextRunnable]);
//   }
// }

interface RawDocument {
  text: string;
  metadata: Record<string, any>;
  vector: number[];
}

// RAG 시스템 클래스
class RAGSystem {
  vectorStore: VectorStore | null;
  embeddings: OpenAIEmbeddings | null;
  llm: ChatOpenAI | null;
  ragChain: RunnableSequence | null;
  isInitialized: boolean;
  constructor() {
    this.vectorStore = null;
    this.embeddings = null;
    this.llm = null;
    this.ragChain = null;
    this.isInitialized = false;
  }

  async initialize() {
    try {
      // 1. OpenAI 임베딩 모델 초기화
      this.embeddings = new OpenAIEmbeddings({
        openAIApiKey: OPENAI_API_KEY,
        modelName: 'text-embedding-3-small',
      });

      // 2. OpenAI 챗 모델 초기화
      this.llm = new ChatOpenAI({
        openAIApiKey: OPENAI_API_KEY,
        modelName: 'gpt-4o-mini',
        temperature: 0.7,
      });

      // 3. 벡터 데이터베이스 로드
      await this.loadVectorStore();

      // 4. RAG 체인 구성
      this.createRAGChain();

      this.isInitialized = true;
      console.log('RAG 시스템 초기화 완료');
      return true;
    } catch (error) {
      console.error('RAG 시스템 초기화 실패:', error);
      throw error;
    }
  }

  async loadVectorStore() {
    try {
      const response = await fetch('./vector_database.json');
      if (!response.ok) {
        throw new Error(`벡터 데이터베이스 로드 실패: ${response.status}`);
      }

      const data = await response.json();

      // data.documents 타입 명시
      const rawDocuments = data.documents as RawDocument[];

      // Document 객체 배열 생성
      const documents = rawDocuments.map(
        (doc: RawDocument) =>
          new Document({
            pageContent: doc.text,
            metadata: doc.metadata,
          })
      );

      // MemoryVectorStore 생성 (기존 벡터 사용)
      this.vectorStore = new MemoryVectorStore(this.embeddings);
      (this.vectorStore as MemoryVectorStore).documents = documents;

      // 기존 벡터 데이터 사용
      (this.vectorStore as MemoryVectorStore).vectors = rawDocuments.map(
        (doc: RawDocument) => doc.vector
      );

      console.log(`${documents.length}개 문서가 벡터 스토어에 로드됨`);
    } catch (error) {
      console.error('벡터 스토어 로드 실패:', error);
      throw error;
    }
  }

  createRAGChain() {
    // RAG 프롬프트 템플릿
    const ragPromptTemplate = PromptTemplate.fromTemplate(`
다음의 컨텍스트를 활용해서 늘봄학교에 대한 질문에 답변해줘.

컨텍스트:
{context}

질문: {question}

답변 지침:
- 질문에 대한 정확하고 도움이 되는 답변을 제공해줘
- 간결하고 이해하기 쉽게 설명해줘
- 친근하고 따뜻한 톤으로 답변해줘
- 컨텍스트에 정보가 없다면 솔직히 모른다고 해줘

답변:`);

    // 문서 포맷터 (컨텍스트 생성)
    const formatDocuments = (docs: Document[]) => {
      return docs.map((doc: Document) => doc.pageContent).join('\n\n');
    };

    // RAG 체인 구성
    this.ragChain = {
      invoke: async (input) => {
        // 1. 관련 문서 검색
        const relevantDocs = await this.vectorStore.similaritySearch(
          input.question,
          4
        );

        // 2. 컨텍스트 생성
        const context = formatDocuments(relevantDocs);

        // 3. 프롬프트 생성
        const prompt = ragPromptTemplate.format({
          context: context,
          question: input.question,
        });

        // 4. LLM 호출
        const response = await this.llm.invoke([
          {
            role: 'user',
            content: prompt,
          },
        ]);

        return {
          answer: response.content,
          sourceDocuments: relevantDocs,
        };
      },
    };
  }

  async query(question) {
    if (!this.isInitialized) {
      throw new Error('RAG 시스템이 초기화되지 않았습니다.');
    }

    return await this.ragChain.invoke({ question });
  }
}

// 늘봄학교 관련 추천 질문들
const SUGGESTED_QUESTIONS = [
  '늘봄학교는 무엇인가요?',
  '늘봄학교 신청 방법을 알려주세요',
  '늘봄학교 운영 시간은 어떻게 되나요?',
  '늘봄학교 프로그램에는 어떤 것들이 있나요?',
  '늘봄학교 이용료는 얼마인가요?',
  '늘봄학교 급식은 어떻게 제공되나요?',
];

const ChatMessage = ({ message, isUser, onCopy }) => {
  const formatTime = (date) => {
    return date.toLocaleTimeString('ko-KR', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[80%] ${isUser ? 'order-2' : 'order-1'}`}>
        <div
          className={`flex items-start space-x-2 ${
            isUser ? 'flex-row-reverse space-x-reverse' : ''
          }`}
        >
          {/* 아바타 */}
          <div
            className={`size-8 rounded-full flex items-center justify-center shrink-0 ${
              isUser
                ? 'bg-blue-500'
                : 'bg-gradient-to-r from-green-500 to-blue-500'
            }`}
          >
            {isUser ? (
              <User className='size-4 text-white' />
            ) : (
              <BookOpen className='size-4 text-white' />
            )}
          </div>

          {/* 메시지 버블 */}
          <div
            className={`relative px-4 py-2 rounded-2xl ${
              isUser ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-900'
            }`}
          >
            <p className='text-sm whitespace-pre-wrap leading-relaxed'>
              {message.content}
            </p>

            {/* 참고문서 */}
            {!isUser && message.reference && (
              <div className='mt-3 p-3 bg-white rounded-lg border border-gray-200'>
                <div className='flex items-center gap-2 text-sm text-gray-600 mb-1'>
                  <FileText size={14} />
                  <span className='font-medium'>참고문서</span>
                </div>
                <div className='text-sm text-gray-700'>
                  {message.reference.fileName} p. {message.reference.page}
                </div>
              </div>
            )}

            {/* 메시지 액션 */}
            {!isUser && (
              <div className='flex items-center justify-between mt-2 pt-2 border-t border-gray-200'>
                <span className='text-xs text-gray-500'>
                  {formatTime(message.timestamp)}
                </span>
                <div className='flex items-center space-x-1'>
                  <button
                    onClick={() => onCopy(message.content)}
                    className='p-1 text-gray-400 hover:text-gray-600 transition-colors'
                    title='복사'
                  >
                    <Copy className='size-3' />
                  </button>
                  <button
                    className='p-1 text-gray-400 hover:text-green-600 transition-colors'
                    title='도움됨'
                  >
                    <ThumbsUp className='size-3' />
                  </button>
                  <button
                    className='p-1 text-gray-400 hover:text-red-600 transition-colors'
                    title='도움 안됨'
                  >
                    <ThumbsDown className='size-3' />
                  </button>
                </div>
              </div>
            )}

            {isUser && (
              <div className='flex justify-end mt-1'>
                <span className='text-xs text-blue-200'>
                  {formatTime(message.timestamp)}
                </span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

const App = () => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      content:
        '안녕하세요! 늘봄학교에 대한 궁금한 점을 도와드리겠습니다. 언제든 질문해 주세요! 🌱',
      isUser: false,
      timestamp: new Date(),
    },
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [ragSystem, setRagSystem] = useState(null);
  const [isInitialized, setIsInitialized] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // RAG 시스템 초기화
  useEffect(() => {
    const initializeRAG = async () => {
      try {
        if (!OPENAI_API_KEY) {
          throw new Error('OpenAI API 키가 설정되지 않았습니다.');
        }

        const rag = new RAGSystem();
        await rag.initialize();

        setRagSystem(rag);
        setIsInitialized(true);
      } catch (err) {
        console.error('RAG 시스템 초기화 실패:', err);
        setError(err.message);
      }
    };

    initializeRAG();
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleCopyMessage = (content) => {
    navigator.clipboard.writeText(content).then(() => {
      // 복사 완료 표시
    });
  };

  const handleQuestionClick = (question) => {
    setInputMessage(question);
    inputRef.current?.focus();
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading || !isInitialized || !ragSystem)
      return;

    const userMessage = {
      id: Date.now(),
      content: inputMessage,
      isUser: true,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    const currentQuestion = inputMessage;
    setInputMessage('');
    setIsLoading(true);
    setError(null);

    try {
      // LangChain RAG 시스템으로 응답 생성
      const result = await ragSystem.query(currentQuestion);

      // 가장 관련성 높은 문서 정보 추출
      const bestMatch = result.sourceDocuments && result.sourceDocuments[0];

      const aiMessage = {
        id: Date.now() + 1,
        content: result.answer,
        isUser: false,
        timestamp: new Date(),
        reference: bestMatch
          ? {
              fileName:
                bestMatch.metadata.file_name ||
                bestMatch.metadata.source ||
                '늘봄학교 가이드',
              page: (bestMatch.metadata.page || 0) + 1,
            }
          : null,
      };

      setMessages((prev) => [...prev, aiMessage]);
    } catch (error) {
      console.error('응답 생성 오류:', error);
      setError(error.message);

      const errorMessage = {
        id: Date.now() + 1,
        content: `죄송합니다. 오류가 발생했습니다: ${error.message}`,
        isUser: false,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  if (!OPENAI_API_KEY) {
    return (
      <div className='bg-white rounded-xl shadow-lg border border-gray-100 h-screen flex flex-col items-center justify-center'>
        <AlertCircle className='size-12 text-red-500 mb-4' />
        <h3 className='text-lg font-semibold text-gray-900 mb-2'>
          API 키가 필요합니다
        </h3>
        <p className='text-sm text-gray-600 text-center max-w-md'>
          .env 파일에 VITE_OPENAI_API_KEY를 설정해주세요.
        </p>
      </div>
    );
  }

  return (
    <div className='bg-white rounded-xl shadow-lg border border-gray-100 h-screen flex flex-col'>
      {/* 헤더 */}
      <div className='p-4 border-b border-gray-200 bg-gradient-to-r from-green-50 to-blue-50 rounded-t-xl'>
        <div className='flex items-center justify-between'>
          <div className='flex items-center space-x-3'>
            <div className='size-10 bg-gradient-to-r from-green-500 to-blue-500 rounded-full flex items-center justify-center'>
              <BookOpen className='size-6 text-white' />
            </div>
            <div>
              <h3 className='font-bold text-gray-900'>늘봄학교 Q&A 챗봇</h3>
              <p className='text-sm text-gray-600'>
                {isInitialized
                  ? 'LangChain 기반 RAG 시스템'
                  : '시스템 초기화 중...'}
              </p>
            </div>
          </div>
          <div className='flex items-center space-x-2'>
            <div
              className={`size-2 rounded-full ${
                isInitialized ? 'bg-green-500' : 'bg-yellow-500'
              }`}
            ></div>
            <button
              className='p-2 text-gray-400 hover:text-gray-600 transition-colors rounded-lg hover:bg-white'
              title='닫기'
            >
              <X className='size-5' />
            </button>
          </div>
        </div>
      </div>

      {/* 에러 표시 */}
      {error && (
        <div className='mx-4 mt-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center space-x-2'>
          <AlertCircle className='size-4 text-red-500' />
          <p className='text-sm text-red-700'>{error}</p>
        </div>
      )}

      {/* 메시지 영역 */}
      <div className='flex-1 overflow-y-auto p-4 space-y-4'>
        {messages.length === 1 && isInitialized ? (
          <div className='text-center py-8'>
            <div className='size-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4'>
              <Sparkles className='size-8 text-green-500' />
            </div>
            <h4 className='font-medium text-gray-900 mb-2'>
              늘봄학교 도우미입니다! 🌱
            </h4>
            <p className='text-sm text-gray-600 mb-4'>
              LangChain을 활용한 AI가 늘봄학교에 대한 질문에 답변해드려요!
            </p>

            {/* 추천 질문들 */}
            <div className='space-y-2'>
              <p className='text-xs text-gray-500'>💡 추천 질문:</p>
              <div className='grid grid-cols-1 gap-2 max-w-md mx-auto'>
                {SUGGESTED_QUESTIONS.slice(0, 4).map((question, index) => (
                  <button
                    key={index}
                    onClick={() => handleQuestionClick(question)}
                    className='text-left px-3 py-2 text-sm bg-green-50 text-green-700 rounded-lg hover:bg-green-100 transition-colors'
                  >
                    {question}
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          messages.map((message) => (
            <ChatMessage
              key={message.id}
              message={message}
              isUser={message.isUser}
              onCopy={handleCopyMessage}
            />
          ))
        )}

        {/* 로딩 인디케이터 */}
        {isLoading && (
          <div className='flex justify-start'>
            <div className='max-w-[80%]'>
              <div className='flex items-start space-x-2'>
                <div className='size-8 bg-gradient-to-r from-green-500 to-blue-500 rounded-full flex items-center justify-center'>
                  <BookOpen className='size-4 text-white' />
                </div>
                <div className='bg-gray-100 px-4 py-2 rounded-2xl'>
                  <div className='flex space-x-1'>
                    <div className='size-2 bg-gray-400 rounded-full animate-bounce'></div>
                    <div className='size-2 bg-gray-400 rounded-full animate-bounce animation-delay-100'></div>
                    <div className='size-2 bg-gray-400 rounded-full animate-bounce animation-delay-200'></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* 추천 질문 영역 */}
      {messages.length > 1 && isInitialized && (
        <div className='px-4 py-2 border-t border-gray-100'>
          <div className='flex flex-wrap gap-2'>
            {SUGGESTED_QUESTIONS.slice(0, 3).map((question, index) => (
              <button
                key={index}
                onClick={() => handleQuestionClick(question)}
                className='px-3 py-1 text-xs bg-gray-100 text-gray-600 rounded-full hover:bg-gray-200 transition-colors flex items-center space-x-1'
                disabled={isLoading}
              >
                <HelpCircle className='size-3' />
                <span className='truncate max-w-32'>{question}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* 입력 영역 */}
      <div className='p-4 border-t border-gray-200'>
        <div className='flex items-end space-x-2'>
          <div className='flex-1'>
            <input
              ref={inputRef}
              type='text'
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={
                isInitialized
                  ? '늘봄학교에 대해 궁금한 것을 물어보세요...'
                  : 'LangChain 시스템 초기화 중...'
              }
              className='w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-green-500 disabled:bg-gray-100'
              disabled={isLoading || !isInitialized}
            />
          </div>
          <button
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || isLoading || !isInitialized}
            className='p-3 bg-gradient-to-r from-green-500 to-blue-500 text-white rounded-xl hover:from-green-600 hover:to-blue-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed'
          >
            <Send className='size-5' />
          </button>
        </div>

        <div className='flex items-center justify-between mt-2 text-xs text-gray-500'>
          <span>Enter로 전송 | LangChain RAG 시스템</span>
          <div className='flex items-center space-x-2'>
            <MessageCircle className='size-3' />
            <span>{messages.length - 1}개 메시지</span>
            <div
              className={`size-2 rounded-full ${
                isInitialized ? 'bg-green-500' : 'bg-yellow-500'
              }`}
            ></div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;
