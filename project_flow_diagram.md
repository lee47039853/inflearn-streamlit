# 소득세 챗봇 프로젝트 호출 흐름

## 시스템 아키텍처

이 프로젝트는 Streamlit 기반의 RAG(Retrieval-Augmented Generation) 시스템으로, 사용자와 관리자 모드를 분리하여 운영됩니다.

## 호출 흐름 다이어그램

```mermaid
sequenceDiagram
    participant User as 사용자
    participant Browser as 브라우저
    participant Launcher as 런처
    participant App as 사용자 앱<br/>(app.py)
    participant Admin as 관리자 앱<br/>(admin.py)
    participant SharedRAG as SharedRAGManager
    participant Embedding as EmbeddingManager
    participant Database as DatabaseManager
    participant EnhancedRAG as EnhancedRAGSystem
    participant LLM as Google Gemini
    participant Chroma as Chroma DB

    Note over User,Chroma: 🚀 시스템 시작
    User->>Launcher: 런처 실행
    Launcher->>Launcher: 의존성 검사
    Launcher->>User: 모드 선택 (사용자/관리자/동시)

    alt 사용자 모드 실행
        Launcher->>App: Streamlit 앱 시작 (포트 8501)
        App->>Browser: 웹 인터페이스 로드
        User->>Browser: 소득세 질문 입력
        Browser->>App: 질문 전송

        App->>SharedRAG: 사용자 세션 생성
        SharedRAG->>Embedding: 임베딩 모델 생성/캐시
        alt 한국어 모델 (ko-sroberta)
            Embedding->>Embedding: HuggingFace 모델 로드
        else Google Gemini
            Embedding->>LLM: Gemini 임베딩 모델 로드
        end

        SharedRAG->>Database: 데이터베이스 생성/로드
        Database->>Chroma: Chroma DB 연결
        alt 기존 DB 존재
            Database->>Chroma: 기존 DB 로드
        else 새 DB 생성
            Database->>Database: tax.docx 문서 로드
            Database->>Database: 텍스트 청킹
            Database->>Chroma: 문서 임베딩 및 저장
        end

        SharedRAG->>EnhancedRAG: RAG 시스템 초기화
        EnhancedRAG->>EnhancedRAG: 쿼리 최적화 체인 생성
        EnhancedRAG->>EnhancedRAG: Few-Shot 체인 생성

        App->>EnhancedRAG: 질문 처리 요청
        alt 쿼리 최적화 활성화
            EnhancedRAG->>EnhancedRAG: 세금 용어로 질문 개선
        end

        EnhancedRAG->>Chroma: 관련 문서 검색
        Chroma->>EnhancedRAG: 검색 결과 반환

        EnhancedRAG->>LLM: 컨텍스트 + 질문으로 답변 생성
        LLM->>EnhancedRAG: AI 답변 반환

        EnhancedRAG->>App: 답변 + 참고문서 반환
        App->>Browser: 답변 표시
        Browser->>User: 소득세 답변 제공

    else 관리자 모드 실행
        Launcher->>Admin: Streamlit 관리자 앱 시작 (포트 8502)
        Admin->>Browser: 관리자 대시보드 로드
        User->>Browser: 시스템 관리 작업
        Browser->>Admin: 관리 명령 전송

        Admin->>SharedRAG: 시스템 상태 확인
        SharedRAG->>Database: DB 상태 조회
        Database->>Admin: 시스템 정보 반환

        Admin->>Database: DB 백업/복원/초기화
        Database->>Chroma: 데이터베이스 작업 수행
        Chroma->>Admin: 작업 결과 반환

        Admin->>Browser: 관리 결과 표시
        Browser->>User: 시스템 관리 완료
    end

    Note over User,Chroma: 💬 대화 지속
    loop 사용자 질문 반복
        User->>Browser: 추가 질문
        Browser->>App: 질문 전송
        App->>EnhancedRAG: 질문 처리
        EnhancedRAG->>Chroma: 문서 검색
        Chroma->>EnhancedRAG: 검색 결과
        EnhancedRAG->>LLM: 답변 생성
        LLM->>EnhancedRAG: AI 답변
        EnhancedRAG->>App: 답변 반환
        App->>Browser: 답변 표시
        Browser->>User: 답변 제공
    end

    Note over User,Chroma: 🛑 시스템 종료
    User->>Launcher: Ctrl+C 또는 종료
    Launcher->>App: 앱 프로세스 종료
    Launcher->>Admin: 관리자 앱 종료
    Launcher->>User: 시스템 종료 완료
```

## 주요 구성 요소

### 1. 런처 시스템

- **launcher.py**: 통합 런처 (사용자/관리자 모드 선택)
- **run.py**: 사용자 모드 전용 실행 스크립트
- **run_admin.py**: 관리자 모드 전용 실행 스크립트

### 2. 사용자 인터페이스

- **app.py**: 메인 챗봇 인터페이스 (포트 8501)
- 소득세 질문 입력 및 AI 답변 제공
- 자동 시스템 초기화 및 API 키 관리

### 3. 관리자 인터페이스

- **admin.py**: 시스템 관리 대시보드 (포트 8502)
- 데이터베이스 상태 모니터링
- 백업/복원/초기화 기능

### 4. RAG 엔진 (retrieval/)

- **shared_rag_manager.py**: 싱글톤 패턴의 공유 리소스 관리
- **enhanced_rag.py**: 향상된 RAG 시스템 (쿼리 최적화, Few-Shot)
- **embedding_manager.py**: 임베딩 모델 관리 (한국어/Gemini)
- **database_manager.py**: Chroma 벡터 DB 관리
- **conversation_history.py**: 대화 기록 관리

## 시스템 특징

1. **이중 포트 구조**: 사용자(8501)와 관리자(8502) 모드 분리
2. **싱글톤 패턴**: 리소스 공유 및 캐싱으로 성능 최적화
3. **모듈화된 RAG**: 쿼리 최적화 및 Few-Shot 학습 지원
4. **하이브리드 임베딩**: 한국어 특화 모델과 Google Gemini 모델
5. **자동 초기화**: API 키 입력 시 자동으로 시스템 구성
6. **대화 기록 관리**: Streamlit 세션 상태로 대화 이력 유지

## 실행 방법

```bash
# 통합 런처 (대화형 모드)
python launcher.py

# 사용자 모드만 실행
python launcher.py user

# 관리자 모드만 실행
python launcher.py admin

# 두 모드 동시 실행
python launcher.py both
```
