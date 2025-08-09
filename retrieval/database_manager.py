"""
데이터베이스 관리 모듈
"""

import shutil
from pathlib import Path
from langchain_community.document_loaders import Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from .config import Config


class DatabaseManager:
    """데이터베이스 관리 클래스"""
    
    def __init__(self, chroma_dir: str = Config.CHROMA_DIR):
        self.chroma_dir = Path(chroma_dir)
    
    def check_existing_database(self) -> bool:
        """기존 Chroma 데이터베이스 존재 여부 확인"""
        return self.chroma_dir.exists() and any(self.chroma_dir.iterdir())
    
    def clear_database(self):
        """기존 데이터베이스 삭제"""
        if self.chroma_dir.exists():
            shutil.rmtree(self.chroma_dir)
            print("🗑️  기존 데이터베이스가 삭제되었습니다.")
            return True
        else:
            print("📂 삭제할 데이터베이스가 없습니다.")
            return False
    
    def get_database_info(self):
        """데이터베이스 정보 반환"""
        info = {
            'exists': self.check_existing_database(),
            'path': str(self.chroma_dir),
            'size_mb': 0,
            'file_count': 0
        }
        
        if info['exists']:
            # 데이터베이스 크기 및 파일 수 계산
            total_size = 0
            file_count = 0
            
            for file_path in self.chroma_dir.rglob('*'):
                if file_path.is_file():
                    file_count += 1
                    total_size += file_path.stat().st_size
            
            info['size_mb'] = round(total_size / (1024 * 1024), 2)
            info['file_count'] = file_count
        
        return info
    
    def backup_database(self, backup_path: str = None):
        """데이터베이스 백업"""
        if not self.check_existing_database():
            print("❌ 백업할 데이터베이스가 없습니다.")
            return False
        
        try:
            import datetime
            if backup_path is None:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"./chroma_backup_{timestamp}"
            
            shutil.copytree(self.chroma_dir, backup_path)
            print(f"✅ 데이터베이스 백업 완료: {backup_path}")
            return True
        except Exception as e:
            print(f"❌ 데이터베이스 백업 실패: {e}")
            return False
    
    def create_database(self, embedding, collection_name: str = 'chroma-tax'):
        """Chroma 데이터베이스 생성"""
        return Chroma(
            collection_name=collection_name,
            persist_directory=str(self.chroma_dir),
            embedding_function=embedding
        )
    
    def load_documents(self, document_path: str = Config.DOCUMENT_PATH):
        """문서 로딩 및 분할"""
        print("📄 문서 로딩 중...")
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP,
        )
        
        loader = Docx2txtLoader(document_path)
        document_list = loader.load_and_split(text_splitter=text_splitter)
        
        print(f"✅ {len(document_list)}개의 문서 청크로 분할 완료")
        return document_list 