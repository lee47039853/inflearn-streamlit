#!/usr/bin/env python3
"""
RAGManager CLI 테스트 스크립트
기존 admin_cli.py를 RAGManager로 대체한 간단한 CLI 도구
"""

import os
import argparse
from dotenv import load_dotenv
from retrieval import RAGManager

def get_user_input(prompt: str, choices: list = None) -> str:
    """사용자 입력 받기"""
    while True:
        try:
            if choices:
                print(f"\n{prompt}")
                for i, choice in enumerate(choices, 1):
                    print(f"{i}. {choice}")
                
                user_input = input(f"\n선택하세요 (1-{len(choices)}): ").strip()
                if user_input.isdigit() and 1 <= int(user_input) <= len(choices):
                    return user_input
                else:
                    print(f"❌ 1-{len(choices)} 중에서 선택하세요.")
            else:
                user_input = input(f"{prompt}: ").strip()
                if user_input:
                    return user_input
                print("❌ 입력이 필요합니다.")
        except KeyboardInterrupt:
            print("\n👋 프로그램을 종료합니다.")
            exit()

def interactive_chat(rag_manager: RAGManager):
    """대화형 채팅 모드"""
    print("\n🤖 RAG 챗봇과 대화를 시작합니다!")
    print("📝 도움말:")
    print("  - 'quit', 'exit': 종료")
    print("  - 'history': 대화 기록 보기")
    print("  - 'clear': 대화 기록 초기화")
    print("  - 'status': 시스템 상태 확인")
    print("  - 'toggle': 쿼리 최적화 토글")
    print("-" * 50)
    
    while True:
        try:
            question = input("\n질문> ").strip()
            
            if not question:
                continue
                
            if question.lower() in ['quit', 'exit', '종료']:
                print("👋 대화를 종료합니다.")
                break
            elif question.lower() == 'history':
                history = rag_manager.get_conversation_history()
                if history:
                    print(f"\n📝 대화 기록 ({len(history)}개):")
                    for i, exchange in enumerate(history[-5:], 1):  # 최근 5개만
                        print(f"{i}. Q: {exchange['question'][:50]}...")
                        print(f"   A: {exchange['answer'][:50]}...")
                else:
                    print("📝 대화 기록이 없습니다.")
                continue
            elif question.lower() == 'clear':
                rag_manager.clear_history()
                continue
            elif question.lower() == 'status':
                status = rag_manager.get_system_status()
                print(f"\n📊 시스템 상태:")
                print(f"  임베딩: {status['embedding_model']}")
                print(f"  최적화: {'✅' if status['query_optimization'] else '❌'}")
                print(f"  대화 수: {status['history_count']}")
                continue
            elif question.lower() == 'toggle':
                rag_manager.toggle_query_optimization()
                continue
            
            # 실제 질문 처리
            print("🔍 처리 중...")
            result = rag_manager.process_query(question)
            
            if result["success"]:
                print(f"\n✅ 답변:")
                print(result["answer"])
                
                # 참고 문서 (간단히)
                if result.get("retrieved_docs"):
                    print(f"\n📚 참고 문서 ({len(result['retrieved_docs'])}개)")
            else:
                print(f"\n❌ 오류: {result['answer']}")
                
        except KeyboardInterrupt:
            print("\n👋 대화를 종료합니다.")
            break
        except Exception as e:
            print(f"❌ 오류 발생: {e}")

def single_question_mode(rag_manager: RAGManager, question: str):
    """단일 질문 모드"""
    print(f"🔍 질문: {question}")
    print("처리 중...")
    
    try:
        result = rag_manager.process_query(question)
        
        if result["success"]:
            print(f"\n✅ 답변:")
            print(result["answer"])
            
            if result.get("retrieved_docs"):
                print(f"\n📚 {len(result['retrieved_docs'])}개 문서 참조")
        else:
            print(f"\n❌ 오류: {result['answer']}")
            
    except Exception as e:
        print(f"❌ 처리 실패: {e}")

def main():
    parser = argparse.ArgumentParser(description='RAGManager CLI 테스트 도구')
    parser.add_argument('--embedding', '-e', choices=['1', '2'], default='1',
                       help='임베딩 모델 (1: 한국어, 2: Google)')
    parser.add_argument('--api-key', '-k', 
                       help='Google API 키 (없으면 환경변수 사용)')
    parser.add_argument('--question', '-q',
                       help='단일 질문 (없으면 대화형 모드)')
    parser.add_argument('--no-optimization', action='store_true',
                       help='쿼리 최적화 비활성화')
    
    args = parser.parse_args()
    
    # .env 파일 로드
    load_dotenv()
    
    # API 키 확인
    api_key = args.api_key or os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("❌ Google API 키가 필요합니다.")
        print("   --api-key 옵션 또는 .env 파일에 GOOGLE_API_KEY 설정")
        return 1
    
    # 설정 출력
    embedding_name = "한국어 특화" if args.embedding == '1' else "Google Gemini"
    optimization = not args.no_optimization
    
    print("🚀 RAGManager CLI 시작")
    print(f"📊 임베딩 모델: {embedding_name}")
    print(f"🔧 쿼리 최적화: {'✅' if optimization else '❌'}")
    print(f"💾 데이터베이스: ./chroma (CLI 전용)")
    print("-" * 50)
    
    try:
        # RAGManager 초기화
        print("🔄 RAG 시스템 초기화 중...")
        rag_manager = RAGManager(
            embedding_choice=args.embedding,
            use_query_optimization=optimization,
            google_api_key=api_key
        )
        print("✅ 초기화 완료!")
        
        # 모드 실행
        if args.question:
            single_question_mode(rag_manager, args.question)
        else:
            interactive_chat(rag_manager)
            
    except Exception as e:
        print(f"❌ 시스템 초기화 실패: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
