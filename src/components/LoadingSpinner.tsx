// src/components/LoadingSpinner.tsx
import React from 'react';

export const LoadingSpinner: React.FC = () => {
  return (
    <div className='flex items-center space-x-2'>
      <div className='animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600'></div>
      <span className='text-sm text-gray-500'>답변을 생성하고 있습니다...</span>
    </div>
  );
};
