from typing import Dict, Any, List
from .chroma_service import ChromaService
from .openai_service import OpenAIService
from openai.types.chat import ChatCompletionMessageParam


class LangChainService:
    """LangChain 통합 서비스"""

    def __init__(self, chroma_service: ChromaService, openai_service: OpenAIService):
        self.chroma_service = chroma_service
        self.openai_service = openai_service

    def process_query(self, query: str) -> Dict[str, Any]:
        """쿼리 처리 및 응답 생성"""
        try:
            # 1. 관련 문서 검색
            search_results = self.chroma_service.similarity_search(query, k=5)

            # 2. 컨텍스트 구성
            context = self._build_context(search_results)

            # 3. 시스템 프롬프트 생성
            system_prompt = self._get_system_prompt()

            # 4. 메시지 구성
            messages: List[ChatCompletionMessageParam] = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"컨텍스트: {context}\n\n질문: {query}"},
            ]

            # 5. AI 응답 생성
            answer = self.openai_service.generate_response(messages)

            return {
                "answer": answer,
                "sources": search_results,
                "context_used": len(search_results) > 0,
            }

        except Exception as e:
            print(f"쿼리 처리 오류: {str(e)}")
            return {
                "answer": "죄송합니다. 요청을 처리하는 중 오류가 발생했습니다.",
                "sources": [],
                "context_used": False,
            }

    def _build_context(self, search_results: List[Dict[str, Any]]) -> str:
        """검색 결과로부터 컨텍스트 구성"""
        if not search_results:
            return "관련 문서를 찾을 수 없습니다."

        context_parts = []
        for i, result in enumerate(search_results[:3], 1):  # 상위 3개만 사용
            source = result.get("metadata", {}).get("source", f"문서 {i}")
            content = result.get("content", "")
            context_parts.append(f"[{source}] {content}")

        return "\n\n".join(context_parts)

    def _get_system_prompt(self) -> str:
        """시스템 프롬프트 반환"""
        return """당신은 늘봄학교 업무 전문 AI 어시스턴트입니다.

다음 지침을 따라 답변해주세요:

1. **정확성**: 제공된 컨텍스트를 바탕으로 정확하고 구체적인 정보를 제공하세요.
2. **친근함**: 따뜻하고 친근한 말투로 답변하되, 전문성을 유지하세요.
3. **구조화**: 답변을 이해하기 쉽게 구조화하여 제시하세요.
4. **한계 인정**: 컨텍스트에 관련 정보가 없으면 솔직하게 말씀드리세요.
5. **부가 정보**: 가능하다면 실용적인 조언이나 추가 정보를 제공하세요.

늘봄학교와 관련된 질문에만 답변하며, 다른 주제의 질문에는 정중히 안내해주세요."""
