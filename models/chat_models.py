from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Optional


@dataclass
class ChatMessage:
    """채팅 메시지 모델"""

    id: str
    content: str
    role: str  # "user" or "assistant"
    timestamp: datetime
    sources: Optional[List[Dict[str, Any]]] = None
    confidence: Optional[int] = None


@dataclass
class ChatSession:
    """채팅 세션 모델"""

    id: Optional[str] = None
    messages: Optional[List[ChatMessage]] = None
    created_at: Optional[datetime] = None

    def __post_init__(self):
        if self.id is None:
            import uuid

            self.id = str(uuid.uuid4())
        if self.messages is None:
            self.messages = []
        if self.created_at is None:
            self.created_at = datetime.now()
