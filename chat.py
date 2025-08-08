import streamlit as st
import os
from dotenv import load_dotenv
from retrieval import RAGManager

# .env 파일 로드
load_dotenv()

# 페이지 설정
st.set_page_config(
    page_title="📚소득세 챗봇", 
    page_icon=":robot_face:",
    layout="wide"
)

# 제목 및 설명
st.title("📚소득세 챗봇")
st.caption("소득세 관련된 모든것을 답해드립니다.")

# 사이드바 설정
with st.sidebar:
    st.header("⚙️ 설정")
    
    # 환경변수에서 Google API 키 가져오기
    env_api_key = os.getenv('GOOGLE_API_KEY')
    
    # Google API 키 입력 (환경변수에 있으면 기본값으로 설정)
    google_api_key = st.text_input(
        "Google API 키", 
        value=env_api_key if env_api_key else "",
        type="password",
        help="Google Gemini API 키를 입력하세요 (또는 .env 파일에 GOOGLE_API_KEY 설정)"
    )
    
    # API 키 상태 표시
    if env_api_key:
        st.success("✅ .env 파일에서 API 키를 찾았습니다!")
    else:
        st.warning("⚠️ .env 파일에 GOOGLE_API_KEY가 설정되지 않았습니다.")
    
    # 임베딩 모델 선택
    embedding_choice = st.selectbox(
        "임베딩 모델",
        options=[
            ("1", "🇰🇷 한국어 특화 (ko-sroberta-multitask)"),
            ("2", "🌐 Google Gemini (embedding-001)")
        ],
        format_func=lambda x: x[1],
        help="문서 검색에 사용할 임베딩 모델을 선택하세요"
    )
    
    # 쿼리 최적화 토글
    use_query_optimization = st.checkbox(
        "쿼리 최적화 사용",
        value=True,
        help="사용자 질문을 세금 관련 용어로 개선하여 검색 정확도를 높입니다"
    )
    
    # 시스템 초기화 버튼
    if st.button("🔄 시스템 초기화", type="primary"):
        # API 키 우선순위: 입력된 키 > 환경변수
        final_api_key = google_api_key if google_api_key else env_api_key
        
        if final_api_key:
            try:
                with st.spinner("RAG 시스템을 초기화하는 중..."):
                    # 세션 상태에 RAG 매니저 저장
                    rag_manager = RAGManager(
                        embedding_choice=embedding_choice[0],
                        use_query_optimization=use_query_optimization,
                        google_api_key=final_api_key
                    )
                    st.session_state.rag_manager = rag_manager
                st.success("✅ RAG 시스템 초기화 완료!")
                st.rerun()  # 상태 업데이트를 위해 페이지 새로고침
            except Exception as e:
                st.error(f"❌ 초기화 실패: {e}")
                st.session_state.rag_manager = None
        else:
            st.error("Google API 키를 입력하거나 .env 파일에 GOOGLE_API_KEY를 설정해주세요.")
    
    # 시스템 상태 표시
    if 'rag_manager' in st.session_state and st.session_state.rag_manager is not None:
        st.divider()
        st.subheader("📊 시스템 상태")
        
        status = st.session_state.rag_manager.get_system_status()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("임베딩 모델", status["embedding_model"])
            st.metric("데이터베이스", "✅ 로드됨" if status["database_loaded"] else "❌ 미로드")
        
        with col2:
            st.metric("LLM", "✅ 로드됨" if status["llm_loaded"] else "❌ 미로드")
            st.metric("대화 기록", status["history_count"])
        
        # 추가 기능
        st.divider()
        st.subheader("🔧 추가 기능")
        
        if st.button("🗑️ 대화 기록 초기화"):
            st.session_state.rag_manager.clear_history()
            st.session_state.messages_list = []
            st.rerun()
        
        if st.button("🔄 쿼리 최적화 토글"):
            st.session_state.rag_manager.toggle_query_optimization()
            st.rerun()

# 메인 채팅 인터페이스
if 'messages_list' not in st.session_state:
    st.session_state.messages_list = []

# RAG 매니저 초기화 상태 확인
if 'rag_manager' not in st.session_state:
    st.session_state.rag_manager = None

# 기존 대화 기록 표시
for message in st.session_state.messages_list:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        
        # AI 응답인 경우 추가 정보 표시
        if message["role"] == "assistant" and "metadata" in message:
            with st.expander("📄 참고 문서"):
                for i, doc in enumerate(message["metadata"].get("retrieved_docs", []), 1):
                    st.write(f"**문서 {i}:**")
                    st.write(doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content)
                    st.divider()

# 사용자 입력 처리
if user_question := st.chat_input(placeholder="소득세에 관련된 궁금한 내용들을 말씀해주세요!"):
    # 사용자 메시지 표시
    with st.chat_message("user"):
        st.write(user_question)
    
    # 세션에 사용자 메시지 추가
    st.session_state.messages_list.append({"role": "user", "content": user_question})
    
    # RAG 시스템이 초기화되지 않은 경우
    if 'rag_manager' not in st.session_state:
        with st.chat_message("assistant"):
            st.error("⚠️ RAG 시스템이 초기화되지 않았습니다. 사이드바에서 Google API 키를 입력하고 시스템을 초기화해주세요.")
        st.session_state.messages_list.append({
            "role": "assistant", 
            "content": "⚠️ RAG 시스템이 초기화되지 않았습니다. 사이드바에서 Google API 키를 입력하고 시스템을 초기화해주세요."
        })
    else:
        # AI 응답 생성
        with st.chat_message("assistant"):
            with st.spinner("🤔 생각 중..."):
                try:
                    # RAG 시스템으로 질문 처리 (Streamlit 호환 방식)
                    if st.session_state.rag_manager is None:
                        raise Exception("RAG 시스템이 초기화되지 않았습니다.")
                    
                    # 직접 호출 (타임아웃은 내부에서 처리)
                    result = st.session_state.rag_manager.process_query(user_question)
                    
                    if result.get("success", False):
                        # 성공적인 응답
                        st.write(result["answer"])
                        
                        # 메타데이터 준비
                        metadata = {
                            "retrieved_docs": result.get("retrieved_docs", []),
                            "improved_query": result.get("improved_query", user_question),
                            "processing_time": result.get("processing_time", 0)
                        }
                        
                        # 세션에 AI 응답 추가
                        st.session_state.messages_list.append({
                            "role": "assistant", 
                            "content": result["answer"],
                            "metadata": metadata
                        })
                        
                        # 참고 문서 표시 (있는 경우)
                        if result.get("retrieved_docs"):
                            with st.expander("📄 참고 문서"):
                                for i, doc in enumerate(result["retrieved_docs"], 1):
                                    st.write(f"**문서 {i}:**")
                                    st.write(doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content)
                                    st.divider()
                    else:
                        # 오류 응답
                        error_msg = result.get("answer", "알 수 없는 오류가 발생했습니다.")
                        st.error(error_msg)
                        st.session_state.messages_list.append({
                            "role": "assistant", 
                            "content": error_msg
                        })
                        
                except Exception as e:
                    error_msg = f"질문 처리 중 오류가 발생했습니다: {e}"
                    st.error(error_msg)
                    st.session_state.messages_list.append({
                        "role": "assistant", 
                        "content": error_msg
                    })

# 하단 정보
st.divider()
st.caption("💡 **사용법**: .env 파일에 API 키를 설정하거나 사이드바에서 입력한 후 시스템을 초기화해보세요!")