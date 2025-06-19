// src/components/MessageBubble.tsx
import React from 'react';
import { Message } from '../models/types';
import { cn } from '../lib/utils';

interface MessageBubbleProps {
  message: Message;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const isUser = message.sender === 'user';

  return (
    <div
      className={cn(
        'flex w-full mb-4',
        isUser ? 'justify-end' : 'justify-start'
      )}
    >
      <div
        className={cn(
          'max-w-[80%] px-4 py-2 rounded-2xl',
          isUser
            ? 'bg-blue-600 text-white rounded-br-md'
            : 'bg-gray-100 text-gray-800 rounded-bl-md'
        )}
      >
        <div className='whitespace-pre-wrap'>{message.content}</div>
        <div
          className={cn(
            'text-xs mt-1 opacity-70',
            isUser ? 'text-blue-100' : 'text-gray-500'
          )}
        >
          {message.timestamp.toLocaleTimeString('ko-KR', {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </div>
      </div>
    </div>
  );
};
