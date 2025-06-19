import { Message, ChatState } from './types';

export class ChatModel {
  private state: ChatState;
  private observers: Array<(state: ChatState) => void> = [];

  constructor() {
    this.state = {
      messages: [],
      isLoading: false,
      error: null,
    };
  }

  // Observer 패턴 구현
  subscribe(observer: (state: ChatState) => void) {
    this.observers.push(observer);
    return () => {
      this.observers = this.observers.filter((obs) => obs !== observer);
    };
  }

  private notify() {
    this.observers.forEach((observer) => observer(this.state));
  }

  // 상태 관리 메서드
  getState(): ChatState {
    return { ...this.state };
  }

  addMessage(message: Omit<Message, 'id' | 'timestamp'>) {
    const newMessage: Message = {
      id: this.generateId(),
      timestamp: new Date(),
      ...message,
    };

    this.state = {
      ...this.state,
      messages: [...this.state.messages, newMessage],
    };
    this.notify();
  }

  setLoading(loading: boolean) {
    this.state = {
      ...this.state,
      isLoading: loading,
    };
    this.notify();
  }

  setError(error: string | null) {
    this.state = {
      ...this.state,
      error,
      isLoading: false,
    };
    this.notify();
  }

  clearMessages() {
    this.state = {
      ...this.state,
      messages: [],
    };
    this.notify();
  }

  private generateId(): string {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }
}
