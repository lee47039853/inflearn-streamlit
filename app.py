import streamlit as st
import os
from dotenv import load_dotenv
from retrieval.shared_rag_manager import SharedRAGManager

# .env 파일 로드
load_dotenv()

# 페이지 설정
st.set_page_config(
    page_title="💬 소득세 챗봇", 
    page_icon=":speech_balloon:",
    layout="centered"
)

# 제목 및 설명
st.title("💬 소득세 챗봇")
st.caption("간단하고 안전한 세금 상담 서비스")

# 환영 메시지
if 'messages_list' not in st.session_state or len(st.session_state.messages_list) == 0:
    with st.container():
        st.info("""
        👋 **안녕하세요!** 
        
        소득세 관련 궁금한 점을 자유롭게 질문해주세요.
        예시: "연봉 5000만원의 소득세는 얼마인가요?"
        """)

# 사이드바 설정 (최소화)
with st.sidebar:
    st.header("⚙️ 간단 설정")
    
    # 환경변수에서 Google API 키 가져오기
    env_api_key = os.getenv('GOOGLE_API_KEY')
    
    # Google API 키 입력 (간단하게)
    if not env_api_key:
        google_api_key = st.text_input(
            "🔑 Google API 키", 
            type="password",
            help="Google AI Studio에서 발급받은 API 키를 입력하세요"
        )
        if google_api_key:
            st.success("✅ API 키가 입력되었습니다!")
    else:
        st.success("✅ API 키가 자동으로 설정되었습니다!")
        google_api_key = env_api_key
    
    # 시스템 자동 초기화 (사용자가 직접 할 필요 없음)
    final_api_key = google_api_key if 'google_api_key' in locals() else env_api_key
    
    # 시스템 상태 표시 (간단하게)
    if 'rag_manager' in st.session_state and st.session_state.rag_manager is not None:
        st.success("🟢 시스템 준비 완료")
        
        # 간단한 통계
        status = st.session_state.rag_manager.get_system_status()
        st.metric("💬 대화 수", status["history_count"])
        
        # 대화 기록 초기화 (간단한 버튼)
        if st.button("🔄 새 대화 시작"):
            st.session_state.rag_manager.clear_history()
            st.session_state.messages_list = []
            st.rerun()
    else:
        if final_api_key:
            st.warning("🟡 시스템 초기화 중...")
        else:
            st.error("🔴 API 키가 필요합니다")
    
    # 도움말
    st.divider()
    st.subheader("❓ 도움말")
    with st.expander("질문 예시"):
        st.write("""
        • 연봉 4000만원의 소득세는?
        • 공제 항목에는 뭐가 있나요?
        • 종합소득세 계산방법은?
        • 세금 신고 시기는 언제인가요?
        """)
    
    with st.expander("시스템 정보"):
        st.write("""
        • 📚 한국 소득세법 기반 답변
        • 🤖 AI 기반 자동 응답
        • 📄 관련 문서 자동 검색
        """)

# 시스템 자동 초기화 (백그라운드)
if 'rag_manager' not in st.session_state:
    st.session_state.rag_manager = None

if 'shared_manager_instance' not in st.session_state:
    st.session_state.shared_manager_instance = SharedRAGManager()

# API 키가 있으면 자동으로 시스템 초기화
if final_api_key and st.session_state.rag_manager is None:
    try:
        with st.spinner("💫 시스템을 준비하고 있습니다..."):
            shared_manager = st.session_state.shared_manager_instance
            
            # 기본 설정으로 자동 초기화 (한국어 모델, 쿼리 최적화 활성화)
            user_session = shared_manager.create_user_session(
                embedding_choice='1',  # 한국어 모델 (기본값)
                use_query_optimization=True,  # 쿼리 최적화 활성화
                google_api_key=final_api_key
            )
            
            st.session_state.rag_manager = user_session
            st.rerun()  # 페이지 새로고침으로 상태 업데이트
    except Exception as e:
        st.error(f"❌ 시스템 준비 중 오류가 발생했습니다: {e}")

# 메인 채팅 인터페이스
if 'messages_list' not in st.session_state:
    st.session_state.messages_list = []

# 기존 대화 기록 표시
for message in st.session_state.messages_list:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# 사용자 입력 처리
if user_question := st.chat_input(placeholder="소득세에 관련된 궁금한 내용을 말씀해주세요!"):
    # 사용자 메시지 표시
    with st.chat_message("user"):
        st.write(user_question)
    
    # 세션에 사용자 메시지 추가
    st.session_state.messages_list.append({"role": "user", "content": user_question})
    
    # RAG 시스템이 초기화되지 않은 경우
    if not final_api_key:
        with st.chat_message("assistant"):
            st.error("🔑 Google API 키를 입력해주세요. 사이드바에서 설정할 수 있습니다.")
        st.session_state.messages_list.append({
            "role": "assistant", 
            "content": "🔑 Google API 키를 입력해주세요. 사이드바에서 설정할 수 있습니다."
        })
    elif st.session_state.rag_manager is None:
        with st.chat_message("assistant"):
            st.warning("⏳ 시스템이 아직 준비 중입니다. 잠시만 기다려주세요.")
        st.session_state.messages_list.append({
            "role": "assistant", 
            "content": "⏳ 시스템이 아직 준비 중입니다. 잠시만 기다려주세요."
        })
    else:
        # AI 응답 생성
        with st.chat_message("assistant"):
            with st.spinner("🤔 답변을 찾고 있습니다..."):
                try:
                    # RAG 시스템으로 질문 처리
                    result = st.session_state.rag_manager.process_query(user_question)
                    
                    if result.get("success", False):
                        # 성공적인 응답
                        st.write(result["answer"])
                        
                        # 세션에 AI 응답 추가
                        st.session_state.messages_list.append({
                            "role": "assistant", 
                            "content": result["answer"]
                        })
                        
                        # 참고 문서 표시 (간단하게)
                        if result.get("retrieved_docs"):
                            with st.expander("📖 참고한 문서들"):
                                doc_count = len(result["retrieved_docs"])
                                st.info(f"총 {doc_count}개의 관련 문서를 참고했습니다.")
                                
                                for i, doc in enumerate(result["retrieved_docs"][:2], 1):  # 최대 2개만 표시
                                    with st.container():
                                        st.write(f"**📄 문서 {i}:**")
                                        content = doc.page_content[:150] + "..." if len(doc.page_content) > 150 else doc.page_content
                                        st.write(content)
                                        if i < min(2, doc_count):
                                            st.divider()
                    else:
                        # 오류 응답
                        error_msg = result.get("answer", "죄송합니다. 답변을 생성할 수 없습니다.")
                        st.warning(error_msg)
                        st.session_state.messages_list.append({
                            "role": "assistant", 
                            "content": error_msg
                        })
                        
                except Exception as e:
                    error_msg = "죄송합니다. 일시적인 오류가 발생했습니다. 다시 시도해주세요."
                    st.error(error_msg)
                    st.session_state.messages_list.append({
                        "role": "assistant", 
                        "content": error_msg
                    })

# 하단 정보
st.divider()
col1, col2 = st.columns([3, 1])
with col1:
    st.caption("💡 **도움이 필요하시면** 사이드바의 도움말을 참고하세요!")
with col2:
    if st.button("🛠️ 관리자", help="관리자 화면으로 이동"):
        st.info("관리자 화면은 별도 포트(8502)에서 실행됩니다.")
        st.code("streamlit run admin.py --server.port 8502")
