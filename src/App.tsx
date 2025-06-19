import { useState, useRef, useEffect } from 'react';
import {
  Send,
  Bot,
  User,
  FileText,
  MessageCircle,
  Sparkles,
  HelpCircle,
  ThumbsUp,
  ThumbsDown,
  Copy,
  X,
} from 'lucide-react';
import '@tailwindcss/theme';

// 벡터 데이터 (실제로는 Python에서 생성된 JSON 파일을 불러와야 함)
const SAMPLE_VECTOR_DATA = {
  documents: [
    {
      id: 0,
      text: '무순위 청약 시에는 부부 중복신청이 가능합니다. 다만, 당첨되면 둘 중 하나는 포기해야 합니다.',
      metadata: {
        file_name: '청약가이드.pdf',
        page: 12,
        source: '청약가이드.pdf',
      },
      vector: [0.1, 0.2, 0.3], // 실제로는 1536차원 벡터
    },
    {
      id: 1,
      text: '1순위 청약자격은 무주택 세대구성원으로 청약저축 가입기간이 2년 이상이어야 합니다.',
      metadata: {
        file_name: '청약가이드.pdf',
        page: 8,
        source: '청약가이드.pdf',
      },
      vector: [0.2, 0.3, 0.4],
    },
    {
      id: 2,
      text: '청약통장은 주택청약종합저축, 청약저축, 청약예금, 청약부금 등이 있습니다.',
      metadata: {
        file_name: '청약매뉴얼.pdf',
        page: 5,
        source: '청약매뉴얼.pdf',
      },
      vector: [0.3, 0.4, 0.5],
    },
  ],
  embedding_model: 'text-embedding-3-small',
};

// 추천 질문들
const SUGGESTED_QUESTIONS = [
  '무순위 청약 시에도 부부 중복신청이 가능한가요?',
  '1순위 청약 자격은 무엇인가요?',
  '청약통장 종류에는 어떤 것들이 있나요?',
  '청약 당첨 확률을 높이는 방법은?',
];

// 간단한 코사인 유사도 계산 (실제로는 더 복잡한 벡터 연산이 필요)
const calculateSimilarity = (vec1, vec2) => {
  const dotProduct = vec1.reduce((sum, a, i) => sum + a * vec2[i], 0);
  const magnitude1 = Math.sqrt(vec1.reduce((sum, a) => sum + a * a, 0));
  const magnitude2 = Math.sqrt(vec2.reduce((sum, a) => sum + a * a, 0));
  return dotProduct / (magnitude1 * magnitude2);
};

// 가상의 OpenAI 임베딩 함수 (실제로는 API 호출 필요)
const getEmbedding = async (text) => {
  // 실제 구현에서는 OpenAI API를 호출해야 함
  return [Math.random(), Math.random(), Math.random()];
};

// 가상의 GPT 응답 생성 함수 (실제로는 OpenAI API 호출 필요)
const generateResponse = async (question, context) => {
  // 실제 구현에서는 OpenAI GPT API를 호출해야 함
  const responses = {
    무순위:
      '무순위 청약 시에는 부부 중복신청이 가능합니다. 다만, 당첨 시 둘 중 하나는 포기해야 합니다.',
    '1순위':
      '1순위 청약자격은 무주택 세대구성원으로 청약저축 가입기간이 2년 이상이어야 합니다.',
    청약통장:
      '청약통장은 주택청약종합저축, 청약저축, 청약예금, 청약부금 등이 있습니다.',
  };

  for (const [key, response] of Object.entries(responses)) {
    if (question.includes(key)) {
      return response;
    }
  }

  return '죄송합니다. 해당 질문에 대한 정보를 찾을 수 없습니다. 다른 질문을 해주세요.';
};

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
                : 'bg-gradient-to-r from-purple-500 to-pink-500'
            }`}
          >
            {isUser ? (
              <User className='size-4 text-white' />
            ) : (
              <Bot className='size-4 text-white' />
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

const PDFChatbot = () => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      content:
        '안녕하세요! 청약 관련 질문을 도와드리겠습니다. 궁금한 것이 있으시면 언제든 물어보세요.',
      isUser: false,
      timestamp: new Date(),
    },
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

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
      // 복사 완료 표시 (간단한 토스트 메시지)
    });
  };

  const handleQuestionClick = (question) => {
    setInputMessage(question);
    inputRef.current?.focus();
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      content: inputMessage,
      isUser: true,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      // 1. 사용자 질문을 임베딩으로 변환
      const questionEmbedding = await getEmbedding(inputMessage);

      // 2. 관련 문서 검색 (코사인 유사도 기반)
      const similarities = SAMPLE_VECTOR_DATA.documents.map((doc) => ({
        ...doc,
        similarity: calculateSimilarity(questionEmbedding, doc.vector),
      }));

      // 3. 가장 유사한 문서 3개 선택
      const topDocs = similarities
        .sort((a, b) => b.similarity - a.similarity)
        .slice(0, 3);

      // 4. GPT로 응답 생성
      const response = await generateResponse(inputMessage, topDocs);

      // 5. 가장 관련성 높은 문서 정보 추출
      const bestMatch = topDocs[0];

      const aiMessage = {
        id: Date.now() + 1,
        content: response,
        isUser: false,
        timestamp: new Date(),
        reference: bestMatch
          ? {
              fileName: bestMatch.metadata.file_name,
              page: bestMatch.metadata.page + 1,
            }
          : null,
      };

      setMessages((prev) => [...prev, aiMessage]);
    } catch (error) {
      console.error('Error generating response:', error);
      const errorMessage = {
        id: Date.now() + 1,
        content: '죄송합니다. 오류가 발생했습니다. 다시 시도해주세요.',
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

  return (
    <div className='bg-white rounded-xl shadow-lg border border-gray-100 h-screen flex flex-col'>
      {/* 헤더 */}
      <div className='p-4 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-purple-50 rounded-t-xl'>
        <div className='flex items-center justify-between'>
          <div className='flex items-center space-x-3'>
            <div className='size-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center'>
              <Bot className='size-6 text-white' />
            </div>
            <div>
              <h3 className='font-bold text-gray-900'>청약 FAQ 챗봇</h3>
              <p className='text-sm text-gray-600'>
                청약 관련 질문을 도와드립니다
              </p>
            </div>
          </div>
          <button
            className='p-2 text-gray-400 hover:text-gray-600 transition-colors rounded-lg hover:bg-white'
            title='닫기'
          >
            <X className='size-5' />
          </button>
        </div>
      </div>

      {/* 메시지 영역 */}
      <div className='flex-1 overflow-y-auto p-4 space-y-4'>
        {messages.length === 1 ? (
          <div className='text-center py-8'>
            <div className='size-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4'>
              <Sparkles className='size-8 text-blue-500' />
            </div>
            <h4 className='font-medium text-gray-900 mb-2'>
              안녕하세요! AI 도우미예요 👋
            </h4>
            <p className='text-sm text-gray-600 mb-4'>
              청약에 대해 궁금한 것이 있으면 언제든 물어보세요!
            </p>

            {/* 추천 질문들 */}
            <div className='space-y-2'>
              <p className='text-xs text-gray-500'>💡 추천 질문:</p>
              <div className='space-y-1'>
                {SUGGESTED_QUESTIONS.slice(0, 2).map((question, index) => (
                  <button
                    key={index}
                    onClick={() => handleQuestionClick(question)}
                    className='block w-full text-left px-3 py-2 text-sm bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 transition-colors'
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
                <div className='size-8 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center'>
                  <Bot className='size-4 text-white' />
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
      {messages.length > 1 && (
        <div className='px-4 py-2 border-t border-gray-100'>
          <div className='flex flex-wrap gap-2'>
            {SUGGESTED_QUESTIONS.slice(0, 2).map((question, index) => (
              <button
                key={index}
                onClick={() => handleQuestionClick(question)}
                className='px-3 py-1 text-xs bg-gray-100 text-gray-600 rounded-full hover:bg-gray-200 transition-colors flex items-center space-x-1'
              >
                <HelpCircle className='size-3' />
                <span>{question}</span>
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
              placeholder='청약에 대해 궁금한 것을 물어보세요...'
              className='w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
              disabled={isLoading}
            />
          </div>
          <button
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || isLoading}
            className='p-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-xl hover:from-blue-600 hover:to-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed'
          >
            <Send className='size-5' />
          </button>
        </div>

        <div className='flex items-center justify-between mt-2 text-xs text-gray-500'>
          <span>Enter로 전송, Shift+Enter로 줄바꿈</span>
          <div className='flex items-center space-x-2'>
            <MessageCircle className='size-3' />
            <span>{messages.length - 1}개 메시지</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PDFChatbot;
