"""
향상된 RAG 시스템 모듈
"""

from typing import List, Dict, Tuple
from langchain import hub
from langchain.chains import RetrievalQA
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from .config import Config


class EnhancedRAGSystem:
    """향상된 RAG 시스템 클래스"""
    
    def __init__(self, database, llm, use_query_optimization: bool = True):
        self.database = database
        self.llm = llm
        self.use_query_optimization = use_query_optimization
        
        # RAG 체인 생성
        self.qa_chain = RetrievalQA.from_chain_type(
            llm, 
            retriever=database.as_retriever(),
            chain_type_kwargs={"prompt": hub.pull("rlm/rag-prompt")}
        )
        
        # 쿼리 개선 체인 생성 (선택적)
        if self.use_query_optimization:
            self.query_improvement_chain = self._create_query_improvement_chain()
            self.integrated_chain = self._create_integrated_chain()
        else:
            self.query_improvement_chain = None
            self.integrated_chain = None
    
    def _create_query_improvement_chain(self):
        """쿼리 개선을 위한 LCEL 체인 생성"""
        prompt = ChatPromptTemplate.from_template(f"""
            사용자의 질문을 보고, 우리의 세금 관련 사전을 참고해서 사용자의 질문을 변경해주세요.
            만약 변경할 필요가 없다고 판단된다면, 사용자의 질문을 변경하지 않아도 됩니다.
            그런 경우에는 질문만 리턴해주세요.
            
            세금 관련 사전: {Config.TAX_DICTIONARY}
            
            질문: {{question}}
            
            개선된 질문:
        """)
        
        return prompt | self.llm | StrOutputParser()
    
    def _create_integrated_chain(self):
        """쿼리 개선과 RAG를 통합한 LCEL 체인 생성"""
        query_improvement = self.query_improvement_chain
        rag_chain = {"query": query_improvement} | self.qa_chain
        return rag_chain
    
    def improve_query(self, query: str) -> str:
        """LLM을 통해 쿼리 개선"""
        if not self.use_query_optimization or self.query_improvement_chain is None:
            return query
        
        try:
            improved_query = self.query_improvement_chain.invoke({"question": query})
            return improved_query.strip()
        except Exception as e:
            print(f"⚠️  쿼리 개선 중 오류: {e}")
            return query
    
    def search_documents(self, query: str, top_k: int = Config.TOP_K_DOCUMENTS) -> List[Tuple]:
        """문서 검색 수행"""
        try:
            results = self.database.similarity_search_with_score(query, k=top_k)
            return results
        except Exception as e:
            print(f"⚠️  검색 중 오류: {e}")
            return []
    
    def process_query_with_improvement(self, query: str) -> Dict:
        """쿼리 개선 후 RAG 처리"""
        print("\n🔧 쿼리 처리:")
        print("=" * 60)
        
        # 1. 쿼리 개선 (선택적)
        print(f"1️⃣ 원본 쿼리: '{query}'")
        if self.use_query_optimization:
            improved_query = self.improve_query(query)
            print(f"2️⃣ 개선된 쿼리: '{improved_query}'")
            search_query = improved_query
        else:
            print("2️⃣ 쿼리 최적화 비활성화 - 원본 쿼리 사용")
            improved_query = query
            search_query = query
        print("-" * 40)
        
        # 2. 쿼리로 문서 검색
        print("3️⃣ 문서 검색 수행 중...")
        retrieved_docs_with_scores = self.search_documents(search_query)
        retrieved_docs = [doc for doc, _ in retrieved_docs_with_scores]
        print(f"   검색된 문서 수: {len(retrieved_docs)}")
        print("-" * 40)
        
        # 3. AI 응답 생성
        print("4️⃣ AI 응답 생성 중...")
        import time
        import threading
        import queue
        
        def run_with_timeout(func, args, timeout=30):
            """타임아웃과 함께 함수 실행 (Streamlit 호환)"""
            import concurrent.futures
            
            try:
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(func, *args)
                    result = future.result(timeout=timeout)
                    return result
            except concurrent.futures.TimeoutError:
                return None  # 타임아웃
            except Exception as e:
                raise e
        
        try:
            if self.use_query_optimization and self.integrated_chain:
                print("   통합 체인 사용 중...")
                ai_response = run_with_timeout(
                    self.integrated_chain.invoke, 
                    [{"question": query}], 
                    30
                )
                if ai_response is None:
                    raise TimeoutError("AI 응답 생성 시간 초과")
                response_text = ai_response['result']
            else:
                print("   기본 QA 체인 사용 중...")
                result = run_with_timeout(
                    self.qa_chain, 
                    [{"query": search_query}], 
                    30
                )
                if result is None:
                    raise TimeoutError("AI 응답 생성 시간 초과")
                response_text = result['result']
            
        except TimeoutError:
            print("⚠️  AI 응답 생성 시간 초과 (30초)")
            response_text = "죄송합니다. 응답 생성에 시간이 오래 걸리고 있습니다. 다시 시도해주세요."
        except Exception as e:
            print(f"⚠️  AI 응답 생성 중 오류: {e}")
            try:
                # 폴백: 기본 QA 체인으로 재시도
                print("   폴백 체인으로 재시도 중...")
                result = run_with_timeout(
                    self.qa_chain, 
                    [{"query": search_query}], 
                    15
                )
                if result is None:
                    raise TimeoutError("폴백 체인도 시간 초과")
                response_text = result['result']
            except Exception as fallback_error:
                print(f"⚠️  폴백 체인도 실패: {fallback_error}")
                response_text = f"죄송합니다. AI 응답 생성 중 오류가 발생했습니다: {str(e)}"
        
        print("=" * 60)
        
        return {
            'success': True,
            'answer': response_text,
            'original_query': query,
            'improved_query': improved_query,
            'retrieved_docs': retrieved_docs,
            'retrieved_docs_with_scores': retrieved_docs_with_scores,
            'optimization_used': self.use_query_optimization
        }
    
    def toggle_query_optimization(self):
        """쿼리 최적화 기능 토글"""
        self.use_query_optimization = not self.use_query_optimization
        
        if self.use_query_optimization and not self.query_improvement_chain:
            self.query_improvement_chain = self._create_query_improvement_chain()
            self.integrated_chain = self._create_integrated_chain()
            print("✅ 쿼리 최적화 기능이 활성화되었습니다.")
        elif not self.use_query_optimization:
            self.query_improvement_chain = None
            self.integrated_chain = None
            print("🚫 쿼리 최적화 기능이 비활성화되었습니다.")
    
    def get_optimization_status(self) -> Dict:
        """쿼리 최적화 상태 정보 반환"""
        return {
            'enabled': self.use_query_optimization,
            'has_chain': self.query_improvement_chain is not None,
            'dictionary_count': len(Config.TAX_DICTIONARY)
        } 