"""
RAG 시스템 통합 관리 모듈
"""

import os
from typing import Dict, Optional
from langchain_google_genai import GoogleGenerativeAI
from .config import Config
from .embedding_manager import EmbeddingManager
from .database_manager import DatabaseManager
from .enhanced_rag import EnhancedRAGSystem
from .conversation_history import ConversationHistory


class RAGManager:
    """RAG 시스템 통합 관리 클래스"""
    
    def __init__(self, 
                 embedding_choice: str = '1',
                 use_query_optimization: bool = True,
                 google_api_key: Optional[str] = None):
        """
        RAG 매니저 초기화
        
        Args:
            embedding_choice: 임베딩 모델 선택 ('1': 한국어, '2': Google)
            use_query_optimization: 쿼리 최적화 사용 여부
            google_api_key: Google API 키 (필요시)
        """
        self.embedding_choice = embedding_choice
        self.use_query_optimization = use_query_optimization
        self.google_api_key = google_api_key or os.getenv('GOOGLE_API_KEY')
        
        # 컴포넌트 초기화
        self.embedding = None
        self.database = None
        self.llm = None
        self.rag_system = None
        self.conversation_history = None
        
        # 시스템 초기화
        self._initialize_system()
    
    def _initialize_system(self):
        """RAG 시스템 초기화"""
        try:
            # 1. 임베딩 모델 초기화
            self.embedding = EmbeddingManager.create_embedding(self.embedding_choice)
            
            # 2. 데이터베이스 매니저 초기화
            self.db_manager = DatabaseManager()
            
            # 3. 데이터베이스 생성 또는 로드
            if self.db_manager.check_existing_database():
                print("📚 기존 데이터베이스 로딩 중...")
                self.database = self.db_manager.create_database(self.embedding)
            else:
                print("📚 새로운 데이터베이스 생성 중...")
                self._create_new_database()
            
            # 4. LLM 초기화
            if self.google_api_key:
                self.llm = GoogleGenerativeAI(
                    model="gemini-1.5-flash",
                    google_api_key=self.google_api_key
                )
            else:
                print("⚠️ Google API 키가 없어 LLM을 초기화할 수 없습니다.")
                return
            
            # 5. RAG 시스템 초기화
            self.rag_system = EnhancedRAGSystem(
                database=self.database,
                llm=self.llm,
                use_query_optimization=self.use_query_optimization
            )
            
            # 6. 대화 히스토리 초기화
            self.conversation_history = ConversationHistory()
            
            print("✅ RAG 시스템 초기화 완료")
            
        except Exception as e:
            print(f"❌ RAG 시스템 초기화 실패: {e}")
            raise
    
    def _create_new_database(self):
        """새로운 데이터베이스 생성"""
        try:
            # 문서 로딩
            documents = self.db_manager.load_documents()
            
            # 데이터베이스 생성 (문서와 함께)
            self.database = self.db_manager.create_database(self.embedding)
            
            # 문서 추가
            self.database.add_documents(documents)
            
            # 최신 Chroma에서는 persist() 메서드가 자동으로 호출됨
            # self.database.persist()  # 이 줄 제거
            
            print(f"✅ {len(documents)}개 문서로 데이터베이스 생성 완료")
            
        except Exception as e:
            print(f"❌ 데이터베이스 생성 실패: {e}")
            raise
    
    def process_query(self, user_question: str) -> Dict:
        """
        사용자 질문 처리
        
        Args:
            user_question: 사용자 질문
            
        Returns:
            처리 결과 딕셔너리
        """
        if not self.rag_system:
            return {
                "success": False,
                "answer": "RAG 시스템이 초기화되지 않았습니다.",
                "error": "System not initialized"
            }
        
        try:
            # 1. RAG 처리
            result = self.rag_system.process_query_with_improvement(user_question)
            
            # 2. 대화 히스토리에 추가
            if result.get("success", False):
                self.conversation_history.add_exchange(
                    question=user_question,
                    answer=result["answer"],
                    retrieved_docs=result.get("retrieved_docs", [])
                )
            
            return result
            
        except Exception as e:
            error_msg = f"질문 처리 중 오류 발생: {e}"
            print(f"❌ {error_msg}")
            return {
                "success": False,
                "answer": error_msg,
                "error": str(e)
            }
    
    def get_conversation_history(self) -> list:
        """대화 히스토리 반환"""
        return self.conversation_history.history if self.conversation_history else []
    
    def clear_history(self):
        """대화 히스토리 초기화"""
        if self.conversation_history:
            self.conversation_history.clear_history()
    
    def toggle_query_optimization(self):
        """쿼리 최적화 토글"""
        if self.rag_system:
            self.rag_system.toggle_query_optimization()
    
    def get_system_status(self) -> Dict:
        """시스템 상태 반환"""
        return {
            "embedding_model": "한국어 특화" if self.embedding_choice == '1' else "Google Gemini",
            "query_optimization": self.rag_system.get_optimization_status() if self.rag_system else False,
            "database_loaded": self.database is not None,
            "llm_loaded": self.llm is not None,
            "history_enabled": self.conversation_history.history_enabled if self.conversation_history else False,
            "history_count": len(self.conversation_history.history) if self.conversation_history else 0
        } 