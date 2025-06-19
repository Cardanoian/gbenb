// src/components/ChatInterface.tsx
import React, { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { ScrollArea } from './ui/scroll-area';
import { MessageBubble } from './MessageBubble';
import { LoadingSpinner } from './LoadingSpinner';
import { ChatController } from '../controllers/ChatController';
import { ChatState } from '../models/types';
import { Send, RotateCcw, Database } from 'lucide-react';

interface ChatInterfaceProps {
  chatController: ChatController;
  databaseStatus: {
    isConnected: boolean;
    documentCount: number;
  };
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  chatController,
  databaseStatus,
}) => {
  const [chatState, setChatState] = useState<ChatState>(
    chatController.getChatState()
  );
  const [inputMessage, setInputMessage] = useState('');
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // 채팅 상태 변화 구독
    const unsubscribe = chatController.subscribeToChatUpdates(setChatState);
    return unsubscribe;
  }, [chatController]);

  useEffect(() => {
    // 새 메시지가 추가될 때 스크롤을 맨 아래로
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }
  }, [chatState.messages]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || chatState.isLoading) return;

    const message = inputMessage.trim();
    setInputMessage('');

    try {
      await chatController.sendMessage(message);
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleClearChat = () => {
    chatController.clearChat();
  };

  return (
    <div className='flex flex-col h-screen max-w-4xl mx-auto p-4'>
      {/* 헤더 */}
      <Card className='mb-4'>
        <CardHeader className='pb-3'>
          <div className='flex items-center justify-between'>
            <CardTitle className='text-xl font-bold text-blue-600'>
              늘봄학교 업무 도우미
            </CardTitle>
            <div className='flex items-center space-x-2'>
              <div className='flex items-center text-sm text-gray-600'>
                <Database className='w-4 h-4 mr-1' />
                <span
                  className={cn(
                    'px-2 py-1 rounded-full text-xs',
                    databaseStatus.isConnected
                      ? 'bg-green-100 text-green-800'
                      : 'bg-red-100 text-red-800'
                  )}
                >
                  {databaseStatus.isConnected
                    ? `연결됨 (${databaseStatus.documentCount}개 문서)`
                    : '연결 안됨'}
                </span>
              </div>
              <Button
                variant='outline'
                size='sm'
                onClick={handleClearChat}
                disabled={chatState.messages.length === 0}
              >
                <RotateCcw className='w-4 h-4 mr-1' />
                초기화
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* 채팅 영역 */}
      <Card className='flex-1 mb-4'>
        <CardContent className='p-0 h-full'>
          <ScrollArea className='h-full p-4' ref={scrollAreaRef}>
            {chatState.messages.length === 0 && (
              <div className='flex items-center justify-center h-full'>
                <div className='text-center text-gray-500'>
                  <div className='text-lg mb-2'>안녕하세요! 👋</div>
                  <div className='text-sm'>
                    늘봄학교 업무에 관해 궁금한 것이 있으시면 언제든 물어보세요.
                  </div>
                  <div className='text-xs mt-2 text-gray-400'>
                    예: "늘봄학교 운영 시간이 어떻게 되나요?"
                  </div>
                </div>
              </div>
            )}

            {chatState.messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}

            {chatState.isLoading && (
              <div className='flex justify-start mb-4'>
                <div className='bg-gray-100 rounded-2xl rounded-bl-md px-4 py-2'>
                  <LoadingSpinner />
                </div>
              </div>
            )}

            {chatState.error && (
              <div className='bg-red-50 border border-red-200 rounded-lg p-3 mb-4'>
                <div className='text-red-800 text-sm'>❌ {chatState.error}</div>
              </div>
            )}
          </ScrollArea>
        </CardContent>
      </Card>

      {/* 입력 영역 */}
      <Card>
        <CardContent className='p-4'>
          <div className='flex space-x-2'>
            <Input
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder='늘봄학교 업무에 대해 질문해주세요...'
              disabled={chatState.isLoading || !databaseStatus.isConnected}
              className='flex-1'
            />
            <Button
              onClick={handleSendMessage}
              disabled={
                !inputMessage.trim() ||
                chatState.isLoading ||
                !databaseStatus.isConnected
              }
              size='icon'
            >
              <Send className='w-4 h-4' />
            </Button>
          </div>

          {!databaseStatus.isConnected && (
            <div className='text-xs text-red-600 mt-2'>
              데이터베이스에 연결되지 않았습니다. 잠시 후 다시 시도해주세요.
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
