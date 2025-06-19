export interface Message {
  id: string;
  content: string;
  sender: 'user' | 'bot';
  timestamp: Date;
}

export interface ChatState {
  messages: Message[];
  isLoading: boolean;
  error: string | null;
}

export interface ChromaDocument {
  id: string;
  content: string;
  metadata: {
    source?: string;
    category?: string;
    [key: string]: any;
  };
}

export interface SimilaritySearchResult {
  document: ChromaDocument;
  score: number;
}

export interface ChatResponse {
  answer: string;
  sources: ChromaDocument[];
  confidence: number;
}

export interface DatabaseConnection {
  isConnected: boolean;
  collectionName: string;
  documentCount: number;
}

export interface OpenAIConfig {
  apiKey: string;
  model: string;
  temperature: number;
  maxTokens: number;
}
