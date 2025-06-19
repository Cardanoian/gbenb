import { useEffect, useState } from 'react';
import { ChatInterface } from '../components/ChatInterface';
import { ChatController } from '../controllers/ChatController';
import { DatabaseController } from '../controllers/DatabaseController';
import { ChatModel } from '../models/ChatModel';
import { DatabaseModel } from '../models/DatabaseModel';
import { ChromaService } from '../services/ChromaService';
import { OpenAIService } from '../services/OpenAIService';
import { LangChainService } from '../services/LangChainService';
import type { DatabaseConnection } from '../models/types';

// 환경 변수 (실제 프로젝트에서는 .env 파일 사용)
const OPENAI_API_KEY = process.env.VITE_OPENAI_API_KEY || 'your-openai-api-key';
const CHROMA_COLLECTION_NAME =
  process.env.VITE_CHROMA_COLLECTION_NAME || 'neulbom_documents';

export default function Root() {
  const [controllers, setControllers] = useState<{
    chatController: ChatController;
    databaseController: DatabaseController;
  } | null>(null);

  const [databaseStatus, setDatabaseStatus] = useState<DatabaseConnection>({
    isConnected: false,
    collectionName: CHROMA_COLLECTION_NAME,
    documentCount: 0,
  });

  const [initError, setInitError] = useState<string | null>(null);

  useEffect(() => {
    initializeApplication();
  }, []);

  const initializeApplication = async () => {
    try {
      // 1. 서비스 인스턴스 생성
      const chromaService = new ChromaService(CHROMA_COLLECTION_NAME);
      const openaiService = new OpenAIService({
        apiKey: OPENAI_API_KEY,
        model: 'gpt-4.1-mini',
        temperature: 0.3,
        maxTokens: 1000,
      });
      const langChainService = new LangChainService(
        OPENAI_API_KEY,
        chromaService,
        openaiService
      );

      // 2. 모델 인스턴스 생성
      const chatModel = new ChatModel();
      const databaseModel = new DatabaseModel();

      // 3. 컨트롤러 인스턴스 생성
      const chatController = new ChatController(
        chatModel,
        databaseModel,
        langChainService
      );
      const databaseController = new DatabaseController(
        databaseModel,
        chromaService
      );

      // 4. 데이터베이스 초기화
      await databaseController.initializeDatabase();

      // 5. 상태 업데이트
      setControllers({ chatController, databaseController });
      setDatabaseStatus(databaseController.getDatabaseStatus());
      setInitError(null);
    } catch (error) {
      console.error('Application initialization failed:', error);
      setInitError(
        error instanceof Error
          ? error.message
          : '애플리케이션 초기화에 실패했습니다.'
      );
    }
  };

  // 데이터베이스 상태 모니터링
  useEffect(() => {
    if (controllers?.databaseController) {
      const interval = setInterval(() => {
        setDatabaseStatus(controllers.databaseController.getDatabaseStatus());
      }, 5000); // 5초마다 상태 확인

      return () => clearInterval(interval);
    }
  }, [controllers]);

  if (initError) {
    return (
      <div className='flex items-center justify-center min-h-screen bg-gray-50'>
        <div className='bg-white p-8 rounded-lg shadow-lg max-w-md w-full mx-4'>
          <div className='text-center'>
            <div className='text-red-600 text-5xl mb-4'>⚠️</div>
            <h2 className='text-xl font-bold text-gray-800 mb-2'>
              초기화 오류
            </h2>
            <p className='text-gray-600 mb-4'>{initError}</p>
            <button
              onClick={initializeApplication}
              className='bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors'
            >
              다시 시도
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!controllers) {
    return (
      <div className='flex items-center justify-center min-h-screen bg-gray-50'>
        <div className='bg-white p-8 rounded-lg shadow-lg'>
          <div className='flex items-center space-x-3'>
            <div className='animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600'></div>
            <div>
              <div className='font-medium text-gray-800'>초기화 중...</div>
              <div className='text-sm text-gray-600'>
                데이터베이스 연결 및 서비스를 준비하고 있습니다.
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className='min-h-screen bg-gray-50'>
      <ChatInterface
        chatController={controllers.chatController}
        databaseStatus={databaseStatus}
      />
    </div>
  );
}
