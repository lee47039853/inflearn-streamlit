"""
공유 RAG 시스템 관리 모듈
"""

import os
import threading
from typing import Dict, Optional
from langchain_google_genai import GoogleGenerativeAI
from .config import Config
from .embedding_manager import EmbeddingManager
from .database_manager import DatabaseManager
from .enhanced_rag import EnhancedRAGSystem
from .conversation_history import ConversationHistory


class SharedRAGManager:
    """공유 리소스를 활용한 RAG 시스템 관리 클래스"""
    
    _instance = None
    _lock = threading.Lock()
    _shared_resources = {}
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self._shared_resources = {
                'embeddings': {},  # 임베딩 모델별 캐시
                'databases': {},   # 데이터베이스 캐시
                'llms': {}        # LLM 캐시
            }
    
    def get_or_create_embedding(self, embedding_choice: str):
        """임베딩 모델 가져오기 또는 생성 (캐시 활용)"""
        with self._lock:
            if embedding_choice not in self._shared_resources['embeddings']:
                print(f"🔄 임베딩 모델 '{embedding_choice}' 새로 생성 중...")
                embedding = EmbeddingManager.create_embedding(embedding_choice)
                self._shared_resources['embeddings'][embedding_choice] = embedding
            else:
                print(f"✅ 캐시된 임베딩 모델 '{embedding_choice}' 사용")
            
            return self._shared_resources['embeddings'][embedding_choice]
    
    def get_or_create_database(self, embedding_choice: str):
        """데이터베이스 가져오기 또는 생성 (캐시 활용)"""
        # 캐시 확인 (락 없이)
        if embedding_choice in self._shared_resources['databases']:
            print(f"✅ 캐시된 데이터베이스 '{embedding_choice}' 사용")
            return self._shared_resources['databases'][embedding_choice]
        
        # 먼저 임베딩을 준비 (락 없이)
        embedding = self.get_or_create_embedding(embedding_choice)
        
        with self._lock:
            # 다시 한번 확인 (다른 스레드가 생성했을 수 있음)
            if embedding_choice in self._shared_resources['databases']:
                print(f"✅ 캐시된 데이터베이스 '{embedding_choice}' 사용")
                return self._shared_resources['databases'][embedding_choice]
            
            print(f"🔄 데이터베이스 '{embedding_choice}' 새로 생성 중...")
            
            try:
                print("   임베딩 모델 준비 완료")
                
                # 임베딩별 별도 경로 사용
                chroma_dir = f"./chroma_{embedding_choice}"
                db_manager = DatabaseManager(chroma_dir=chroma_dir)
                print(f"   데이터베이스 매니저 생성 완료 (경로: {chroma_dir})")
                
                if db_manager.check_existing_database():
                    print("   기존 데이터베이스 발견, 로딩 중...")
                    database = db_manager.create_database(embedding)
                    print("   기존 데이터베이스 로딩 완료")
                else:
                    print("   새 데이터베이스 생성: 문서 로딩 시작...")
                    documents = db_manager.load_documents()
                    print(f"   문서 로딩 완료: {len(documents)}개 청크")
                    
                    print("   Chroma 데이터베이스 인스턴스 생성 중...")
                    database = db_manager.create_database(embedding)
                    print("   Chroma 데이터베이스 인스턴스 생성 완료")
                    
                    print("   문서 임베딩 및 저장 시작... (시간이 오래 걸릴 수 있습니다)")
                    database.add_documents(documents)
                    print("   문서 임베딩 및 저장 완료")
                
                self._shared_resources['databases'][embedding_choice] = database
                print(f"✅ 데이터베이스 '{embedding_choice}' 생성 완료")
                
                return database
                
            except Exception as e:
                print(f"❌ 데이터베이스 생성 실패: {e}")
                raise
    
    def get_or_create_llm(self, google_api_key: str):
        """LLM 가져오기 또는 생성 (캐시 활용)"""
        with self._lock:
            # API 키의 해시값을 키로 사용 (보안)
            import hashlib
            key_hash = hashlib.md5(google_api_key.encode()).hexdigest()
            
            if key_hash not in self._shared_resources['llms']:
                print("🔄 LLM 새로 생성 중...")
                llm = GoogleGenerativeAI(
                    model="gemini-1.5-flash",
                    google_api_key=google_api_key
                )
                self._shared_resources['llms'][key_hash] = llm
            else:
                print("✅ 캐시된 LLM 사용")
            
            return self._shared_resources['llms'][key_hash]
    
    def create_user_session(self, 
                           embedding_choice: str = '1',
                           use_query_optimization: bool = True,
                           google_api_key: Optional[str] = None):
        """사용자별 개별 세션 생성 (공유 리소스 활용)"""
        
        # 공유 리소스 가져오기
        embedding = self.get_or_create_embedding(embedding_choice)
        database = self.get_or_create_database(embedding_choice)
        llm = self.get_or_create_llm(google_api_key)
        
        # 개별 RAG 시스템 생성 (대화 히스토리는 개별)
        rag_system = EnhancedRAGSystem(
            database=database,
            llm=llm,
            use_query_optimization=use_query_optimization
        )
        
        # 개별 대화 히스토리
        conversation_history = ConversationHistory()
        
        return UserRAGSession(
            rag_system=rag_system,
            conversation_history=conversation_history,
            embedding_choice=embedding_choice,
            google_api_key=google_api_key
        )
    
    def get_database_status(self, embedding_choice: str):
        """특정 임베딩에 대한 데이터베이스 상태 확인"""
        # 임베딩별 별도 경로 사용
        chroma_dir = f"./chroma_{embedding_choice}"
        db_manager = DatabaseManager(chroma_dir=chroma_dir)
        
        return {
            'exists_on_disk': db_manager.check_existing_database(),
            'cached_in_memory': embedding_choice in self._shared_resources['databases'],
            'embedding_choice': embedding_choice,
            'database_path': chroma_dir
        }
    
    def clear_database_cache(self, embedding_choice: str):
        """메모리에서 데이터베이스 캐시 제거"""
        with self._lock:
            if embedding_choice in self._shared_resources['databases']:
                del self._shared_resources['databases'][embedding_choice]
                print(f"🗑️  메모리에서 데이터베이스 '{embedding_choice}' 캐시 제거")
                return True
            return False
    
    def delete_database_files(self, embedding_choice: str = None):
        """디스크에서 데이터베이스 파일 삭제"""
        try:
            if embedding_choice:
                # 특정 임베딩의 데이터베이스만 삭제
                chroma_dir = f"./chroma_{embedding_choice}"
                db_manager = DatabaseManager(chroma_dir=chroma_dir)
                db_manager.clear_database()
                
                # 해당 캐시만 제거
                with self._lock:
                    if embedding_choice in self._shared_resources['databases']:
                        del self._shared_resources['databases'][embedding_choice]
                
                print(f"🗑️  데이터베이스 '{embedding_choice}' 파일 및 캐시 삭제 완료")
            else:
                # 모든 데이터베이스 삭제
                import glob
                chroma_dirs = glob.glob("./chroma*")
                for chroma_dir in chroma_dirs:
                    db_manager = DatabaseManager(chroma_dir=chroma_dir)
                    db_manager.clear_database()
                
                # 모든 캐시 제거
                with self._lock:
                    self._shared_resources['databases'].clear()
                
                print("🗑️  모든 데이터베이스 파일 및 캐시 삭제 완료")
            
            return True
        except Exception as e:
            print(f"❌ 데이터베이스 삭제 실패: {e}")
            return False
    
    def force_recreate_database(self, embedding_choice: str):
        """데이터베이스 강제 재생성"""
        try:
            # 1. 메모리 캐시 제거
            self.clear_database_cache(embedding_choice)
            
            # 2. 해당 임베딩의 디스크 파일 삭제
            self.delete_database_files(embedding_choice)
            
            # 3. 새 데이터베이스 생성
            database = self.get_or_create_database(embedding_choice)
            
            print(f"✅ 데이터베이스 '{embedding_choice}' 강제 재생성 완료")
            return True
        except Exception as e:
            print(f"❌ 데이터베이스 재생성 실패: {e}")
            return False

    def get_resource_status(self):
        """공유 리소스 상태 반환"""
        return {
            'cached_embeddings': list(self._shared_resources['embeddings'].keys()),
            'cached_databases': list(self._shared_resources['databases'].keys()),
            'cached_llms_count': len(self._shared_resources['llms']),
            'total_memory_saved': "High" if len(self._shared_resources['embeddings']) > 0 else "None"
        }


class UserRAGSession:
    """사용자별 개별 RAG 세션"""
    
    def __init__(self, rag_system, conversation_history, embedding_choice, google_api_key):
        self.rag_system = rag_system
        self.conversation_history = conversation_history
        self.embedding_choice = embedding_choice
        self.google_api_key = google_api_key
    
    def process_query(self, user_question: str) -> Dict:
        """사용자 질문 처리"""
        try:
            # RAG 처리
            result = self.rag_system.process_query_with_improvement(user_question)
            
            # 대화 히스토리에 추가
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
        return self.conversation_history.history
    
    def clear_history(self):
        """대화 히스토리 초기화"""
        self.conversation_history.clear_history()
    
    def toggle_query_optimization(self):
        """쿼리 최적화 토글"""
        self.rag_system.toggle_query_optimization()
    
    def get_system_status(self) -> Dict:
        """시스템 상태 반환"""
        return {
            "embedding_model": "한국어 특화" if self.embedding_choice == '1' else "Google Gemini",
            "query_optimization": self.rag_system.get_optimization_status() if self.rag_system else False,
            "database_loaded": True,
            "llm_loaded": True,
            "history_enabled": self.conversation_history.history_enabled,
            "history_count": len(self.conversation_history.history)
        }
