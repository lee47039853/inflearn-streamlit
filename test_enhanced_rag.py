"""
향상된 RAG 시스템 테스트 파일
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from retrieval.enhanced_rag import EnhancedRAGSystem
from retrieval.config import Config
from langchain_core.runnables import Runnable
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document

def test_config():
    """Config 설정 테스트"""
    print("🔧 Config 설정 테스트")
    print("=" * 50)
    print(f"세금 사전 항목 수: {len(Config.TAX_DICTIONARY)}")
    print(f"답변 예시 수: {len(Config.ANSWER_EXAMPLES)}")
    print("\n답변 예시:")
    for i, example in enumerate(Config.ANSWER_EXAMPLES, 1):
        print(f"{i}. 질문: {example['question']}")
        print(f"   답변: {example['answer'][:100]}...")
        print()
    print("=" * 50)

def test_enhanced_rag_initialization():
    """EnhancedRAGSystem 초기화 테스트"""
    print("🚀 EnhancedRAGSystem 초기화 테스트")
    print("=" * 50)
    
    # Mock 객체들 (LangChain 인터페이스 구현)
    class MockDatabase(BaseRetriever):
        def as_retriever(self):
            return self
        
        def similarity_search_with_score(self, query, k=5):
            return [("Mock Document 1", 0.9), ("Mock Document 2", 0.8)]
        
        def get_relevant_documents(self, query):
            return [Document(page_content="Mock Document 1"), Document(page_content="Mock Document 2")]
        
        def invoke(self, input_data, config=None):
            return self.get_relevant_documents(input_data)
    
    class MockLLM(Runnable):
        def invoke(self, input_data, config=None):
            if isinstance(input_data, dict) and "question" in input_data:
                return f"Mock response for: {input_data['question']}"
            return "Mock response"
        
        def stream(self, input_data, config=None):
            yield self.invoke(input_data, config)
    
    try:
        # 다양한 설정으로 초기화 테스트
        print("1. 모든 기능 활성화:")
        rag_system = EnhancedRAGSystem(
            database=MockDatabase(),
            llm=MockLLM(),
            use_query_optimization=True,
            use_few_shot=True
        )
        status = rag_system.get_optimization_status()
        print(f"   상태: {status}")
        
        print("\n2. 쿼리 최적화만 활성화:")
        rag_system2 = EnhancedRAGSystem(
            database=MockDatabase(),
            llm=MockLLM(),
            use_query_optimization=True,
            use_few_shot=False
        )
        status2 = rag_system2.get_optimization_status()
        print(f"   상태: {status2}")
        
        print("\n3. Few-Shot만 활성화:")
        rag_system3 = EnhancedRAGSystem(
            database=MockDatabase(),
            llm=MockLLM(),
            use_query_optimization=False,
            use_few_shot=True
        )
        status3 = rag_system3.get_optimization_status()
        print(f"   상태: {status3}")
        
        print("\n4. 기본 RAG만:")
        rag_system4 = EnhancedRAGSystem(
            database=MockDatabase(),
            llm=MockLLM(),
            use_query_optimization=False,
            use_few_shot=False
        )
        status4 = rag_system4.get_optimization_status()
        print(f"   상태: {status4}")
        
        print("\n✅ 모든 초기화 테스트 통과!")
        
    except Exception as e:
        print(f"❌ 초기화 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 50)

def test_functionality_toggle():
    """기능 토글 테스트"""
    print("🔄 기능 토글 테스트")
    print("=" * 50)
    
    class MockDatabase(BaseRetriever):
        def as_retriever(self):
            return self
        
        def similarity_search_with_score(self, query, k=5):
            return [("Mock Document 1", 0.9)]
        
        def get_relevant_documents(self, query):
            return [Document(page_content="Mock Document 1")]
        
        def invoke(self, input_data, config=None):
            return self.get_relevant_documents(input_data)
    
    class MockLLM(Runnable):
        def invoke(self, input_data, config=None):
            return f"Mock response for: {input_data.get('question', 'unknown')}"
        
        def stream(self, input_data, config=None):
            yield self.invoke(input_data, config)
    
    try:
        rag_system = EnhancedRAGSystem(
            database=MockDatabase(),
            llm=MockLLM(),
            use_query_optimization=True,
            use_few_shot=True
        )
        
        print("초기 상태:")
        status = rag_system.get_optimization_status()
        print(f"   {status}")
        
        print("\n쿼리 최적화 토글:")
        rag_system.toggle_query_optimization()
        status = rag_system.get_optimization_status()
        print(f"   {status}")
        
        print("\nFew-Shot 토글:")
        rag_system.toggle_few_shot()
        status = rag_system.get_optimization_status()
        print(f"   {status}")
        
        print("\n다시 원래대로:")
        rag_system.toggle_query_optimization()
        rag_system.toggle_few_shot()
        status = rag_system.get_optimization_status()
        print(f"   {status}")
        
        print("\n✅ 기능 토글 테스트 통과!")
        
    except Exception as e:
        print(f"❌ 기능 토글 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 50)

if __name__ == "__main__":
    print("🧪 EnhancedRAGSystem 테스트 시작")
    print("=" * 60)
    
    test_config()
    print()
    test_enhanced_rag_initialization()
    print()
    test_functionality_toggle()
    
    print("\n🎉 모든 테스트 완료!")
