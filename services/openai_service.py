from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
from typing import Dict, Any, List, Optional
import os


class OpenAIService:
    """OpenAI API 서비스 클래스"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API 키가 설정되지 않았습니다.")

        self.client = OpenAI(api_key=self.api_key)
        self.model = "gpt-3.5-turbo"
        self.temperature = 0.7
        self.max_tokens = 1000

    def generate_response(self, messages: List[ChatCompletionMessageParam]) -> str:
        """GPT를 사용하여 응답 생성"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )

            content = response.choices[0].message.content
            return content.strip() if content else ""

        except Exception as e:
            print(f"OpenAI API 오류: {str(e)}")
            return (
                "죄송합니다. 현재 응답을 생성할 수 없습니다. 잠시 후 다시 시도해주세요."
            )

    def create_embedding(self, text: str) -> List[float]:
        """텍스트 임베딩 생성"""
        try:
            response = self.client.embeddings.create(
                model="text-embedding-ada-002", input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"임베딩 생성 오류: {str(e)}")
            return []
