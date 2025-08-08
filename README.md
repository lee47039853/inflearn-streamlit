# 📚 소득세 챗봇 (RAG 기반)

소득세 관련 질문에 대해 RAG(Retrieval-Augmented Generation) 기술을 활용하여 정확하고 신뢰할 수 있는 답변을 제공하는 Streamlit 기반 챗봇입니다.

## 🚀 주요 기능

- **RAG 시스템**: 문서 기반 정확한 답변 생성
- **쿼리 최적화**: 사용자 질문을 세금 관련 용어로 개선
- **대화 히스토리**: 이전 대화 내용 기억 및 컨텍스트 활용
- **다중 임베딩 모델**: 한국어 특화 모델과 Google Gemini 모델 지원
- **실시간 문서 참조**: 답변에 사용된 참고 문서 표시
- **사용자 친화적 UI**: 직관적인 채팅 인터페이스

## 📋 시스템 요구사항

- Python 3.8 이상
- Google Gemini API 키
- 최소 4GB RAM (임베딩 모델 로딩용)

## 🛠️ 설치 방법

### 1. 저장소 클론

```bash
git clone <repository-url>
cd inflearn-streamlit
```

### 2. 가상환경 생성 및 활성화

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. 의존성 설치

```bash
pip install -r requirements.txt
```

### 4. Google API 키 설정

Google AI Studio에서 API 키를 발급받아 `.env` 파일에 설정하거나, 애플리케이션 실행 시 입력하세요.

#### 방법 1: .env 파일 사용 (권장)

```bash
# .env 파일 생성
cp env_example.txt .env

# .env 파일 편집하여 API 키 입력
# GOOGLE_API_KEY=your-actual-api-key-here
```

#### 방법 2: 환경변수 설정

```bash
# 환경변수 설정 (선택사항)
export GOOGLE_API_KEY="your-api-key-here"
```

## 🎯 사용 방법

### 1. 애플리케이션 실행

```bash
streamlit run chat.py
```

### 2. 시스템 초기화

1. 사이드바에서 Google API 키 입력
2. 임베딩 모델 선택 (한국어 특화 또는 Google Gemini)
3. 쿼리 최적화 옵션 설정
4. "시스템 초기화" 버튼 클릭

### 3. 질문하기

- 채팅 입력창에 소득세 관련 질문 입력
- AI가 관련 문서를 검색하여 답변 생성
- 참고 문서는 확장 가능한 섹션에서 확인

## 📁 프로젝트 구조

```
inflearn-streamlit/
├── chat.py                 # 메인 Streamlit 애플리케이션
├── requirements.txt        # Python 의존성
├── README.md              # 프로젝트 설명서
├── retrieval/             # RAG 시스템 패키지
│   ├── __init__.py        # 패키지 초기화
│   ├── config.py          # 설정 관리
│   ├── rag_manager.py     # RAG 시스템 통합 관리
│   ├── enhanced_rag.py    # 향상된 RAG 시스템
│   ├── database_manager.py # 데이터베이스 관리
│   ├── embedding_manager.py # 임베딩 모델 관리
│   ├── conversation_history.py # 대화 히스토리 관리
│   ├── command_processor.py # 명령어 처리
│   └── user_interface.py  # 사용자 인터페이스
├── tax.docx              # 소득세 관련 문서 (필요시 추가)
└── chroma/               # 벡터 데이터베이스 (자동 생성)
```

## 🔧 주요 컴포넌트

### RAGManager

- RAG 시스템의 통합 관리자
- 임베딩, 데이터베이스, LLM, 대화 히스토리 통합 관리

### EnhancedRAGSystem

- 쿼리 최적화 기능
- 문서 검색 및 답변 생성
- 처리 과정 모니터링

### DatabaseManager

- Chroma 벡터 데이터베이스 관리
- 문서 로딩 및 청킹
- 데이터베이스 생성/로드

### ConversationHistory

- 대화 히스토리 관리
- 컨텍스트 추출 및 활용
- 히스토리 제어 기능

## 🎨 UI 기능

### 사이드바

- **시스템 설정**: API 키, 임베딩 모델, 쿼리 최적화
- **시스템 상태**: 각 컴포넌트 로딩 상태 표시
- **추가 기능**: 대화 기록 초기화, 쿼리 최적화 토글

### 메인 채팅

- **실시간 채팅**: 사용자/AI 메시지 구분 표시
- **참고 문서**: 답변에 사용된 문서 미리보기
- **오류 처리**: 시스템 오류 시 친화적 메시지

## 🔍 사용 예시

### 질문 예시

```
Q: "연봉 5000만원 받는 직장인의 소득세는 얼마인가요?"
A: [RAG 시스템이 관련 문서를 검색하여 정확한 답변 제공]

Q: "공제 항목에는 어떤 것들이 있나요?"
A: [세금 관련 문서에서 공제 항목 정보 검색 후 답변]
```

## ⚠️ 주의사항

1. **API 키 보안**: Google API 키를 안전하게 관리하세요
2. **문서 준비**: `tax.docx` 파일이 필요합니다 (소득세 관련 문서)
3. **인터넷 연결**: 임베딩 모델 다운로드 및 API 호출에 필요
4. **시스템 리소스**: 임베딩 모델 로딩 시 메모리 사용량 증가

## 🐛 문제 해결

### 일반적인 오류

1. **API 키 오류**

   - Google AI Studio에서 올바른 API 키 발급 확인
   - API 키 권한 설정 확인

2. **모델 로딩 실패**

   - 인터넷 연결 확인
   - 충분한 디스크 공간 확보

3. **메모리 부족**
   - 다른 애플리케이션 종료
   - 더 많은 RAM 확보

## 📈 향후 개선 계획

- [ ] 다중 문서 형식 지원 (PDF, TXT 등)
- [ ] 실시간 문서 업데이트 기능
- [ ] 답변 품질 평가 시스템
- [ ] 사용자 피드백 시스템
- [ ] 모바일 최적화

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 문의

프로젝트에 대한 문의사항이 있으시면 이슈를 생성해주세요.
