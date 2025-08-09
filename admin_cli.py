#!/usr/bin/env python3
"""
개선된 관리자 CLI - RAGManager 활용 버전
기존 admin_cli.py의 기능을 RAGManager로 재구현
데이터베이스 관리 기능 추가
"""

import os
from dotenv import load_dotenv
from retrieval import RAGManager
from retrieval.database_manager import DatabaseManager
from retrieval.embedding_manager import EmbeddingManager

def get_user_choice(prompt: str, choices: list) -> str:
    """사용자 선택 받기"""
    print(f"\n{prompt}")
    for i, choice in enumerate(choices, 1):
        print(f"{i}. {choice}")
    
    while True:
        try:
            choice = input(f"\n선택하세요 (1-{len(choices)}): ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(choices):
                return choice
            print(f"❌ 1-{len(choices)} 중에서 선택하세요.")
        except KeyboardInterrupt:
            print("\n👋 프로그램을 종료합니다.")
            exit()

def check_database_status(embedding_choice: str) -> dict:
    """데이터베이스 상태 확인 및 정보 표시"""
    db_manager = DatabaseManager()  # CLI는 기본 ./chroma 경로 사용
    
    # 데이터베이스 상태 확인
    exists = db_manager.check_existing_database()
    
    status = {
        'exists': exists,
        'db_manager': db_manager,
        'embedding_choice': embedding_choice
    }
    
    if exists:
        # 상세 정보 가져오기
        db_info = db_manager.get_database_info()
        status.update(db_info)
        
        print(f"\n💾 데이터베이스 상태:")
        print(f"  📂 경로: {db_info['path']}")
        print(f"  📊 크기: {db_info['size_mb']} MB")
        print(f"  📄 파일 수: {db_info['file_count']}개")
        print(f"  ✅ 상태: 존재함")
    else:
        print(f"\n💾 데이터베이스 상태:")
        print(f"  📂 경로: ./chroma")
        print(f"  ❌ 상태: 존재하지 않음")
    
    return status

def handle_database_choice(db_status: dict, api_key: str) -> RAGManager:
    """데이터베이스 처리 방식에 따라 RAGManager 생성"""
    embedding_choice = db_status['embedding_choice']
    
    if db_status['exists']:
        # 기존 DB가 있는 경우
        db_choice = get_user_choice(
            "💾 기존 데이터베이스 처리 방식:",
            [
                "♻️ 기존 데이터베이스 재사용 (빠름)",
                "🔄 기존 데이터베이스 삭제 후 신규 생성",
                "💿 데이터베이스 백업 후 신규 생성"
            ]
        )
        
        db_manager = db_status['db_manager']
        
        if db_choice == '1':
            # 기존 DB 재사용
            print("♻️ 기존 데이터베이스를 재사용합니다...")
            
        elif db_choice == '2':
            # 기존 DB 삭제 후 신규 생성
            print("🔄 기존 데이터베이스를 삭제합니다...")
            if db_manager.clear_database():
                print("✅ 데이터베이스 삭제 완료")
            else:
                print("⚠️ 데이터베이스 삭제 중 문제 발생")
                
        elif db_choice == '3':
            # 백업 후 신규 생성
            print("💿 기존 데이터베이스를 백업합니다...")
            if db_manager.backup_database():
                print("✅ 백업 완료, 기존 데이터베이스를 삭제합니다...")
                if db_manager.clear_database():
                    print("✅ 데이터베이스 삭제 완료")
                else:
                    print("⚠️ 데이터베이스 삭제 중 문제 발생")
            else:
                print("❌ 백업 실패! 기존 데이터베이스를 유지합니다.")
                print("♻️ 기존 데이터베이스를 재사용합니다...")
    else:
        # DB가 없는 경우
        print("📄 새로운 데이터베이스를 생성합니다...")
        
    # 쿼리 최적화 선택
    optimization_choice = get_user_choice(
        "🔧 쿼리 최적화 기능:",
        [
            "✅ 최적화 활성화 (LLM을 통한 질문 개선) - 추천", 
            "❌ 최적화 비활성화 (원본 질문 그대로)"
        ]
    )
    
    use_optimization = (optimization_choice == '1')
    
    # RAGManager 생성
    print(f"\n🔄 RAG 시스템 초기화 중...")
    print(f"  📊 임베딩: {'한국어 특화' if embedding_choice == '1' else 'Google Gemini'}")
    print(f"  🔧 최적화: {'활성화' if use_optimization else '비활성화'}")
    print(f"  💾 데이터베이스: ./chroma (CLI 전용)")
    
    rag_manager = RAGManager(
        embedding_choice=embedding_choice,
        use_query_optimization=use_optimization,
        google_api_key=api_key
    )
    
    return rag_manager

def main():
    print("🛠️ 소득세 챗봇 관리자 CLI (RAGManager 버전)")
    print("=" * 60)
    
    # .env 파일 로드
    load_dotenv()
    
    # Google API 키 확인
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY가 설정되지 않았습니다.")
        print("   .env 파일에 GOOGLE_API_KEY=your_api_key_here를 추가하세요.")
        return
    
    try:
        # 임베딩 모델 선택
        embedding_choice = get_user_choice(
            "📊 임베딩 모델 선택:",
            [
                "🇰🇷 한국어 특화 (ko-sroberta-multitask) - 추천",
                "🌐 Google Gemini 임베딩"
            ]
        )
        
        # 데이터베이스 상태 확인
        print("\n🔍 데이터베이스 상태를 확인합니다...")
        db_status = check_database_status(embedding_choice)
        
        # 데이터베이스 처리 및 RAGManager 생성
        rag_manager = handle_database_choice(db_status, api_key)
        
        print("✅ RAG 시스템 초기화 완료!")
        print("=" * 60)
        
        # 관리자 메뉴 루프
        while True:
            print("\n🛠️ 관리자 메뉴:")
            print("1. 💬 질문-답변 테스트")
            print("2. 📝 대화 기록 보기")
            print("3. 🗑️ 대화 기록 초기화")
            print("4. 🔧 쿼리 최적화 토글")
            print("5. 📊 시스템 상태 확인")
            print("6. 💾 데이터베이스 관리")
            print("7. 🧪 상세 테스트 모드")
            print("8. ❌ 종료")
            
            try:
                menu_choice = input("\n선택> ").strip()
                
                if menu_choice == '1':
                    # 질문-답변 테스트
                    question = input("\n질문을 입력하세요> ").strip()
                    if question:
                        print("🔍 처리 중...")
                        result = rag_manager.process_query(question)
                        
                        print(f"\n📝 결과:")
                        if result["success"]:
                            print(f"✅ 답변: {result['answer']}")
                            if result.get("retrieved_docs"):
                                print(f"📚 참고 문서: {len(result['retrieved_docs'])}개")
                        else:
                            print(f"❌ 오류: {result['answer']}")
                
                elif menu_choice == '2':
                    # 대화 기록 보기
                    history = rag_manager.get_conversation_history()
                    if history:
                        print(f"\n📝 대화 기록 ({len(history)}개):")
                        print("-" * 60)
                        for i, exchange in enumerate(history, 1):
                            print(f"\n💬 대화 {i}:")
                            print(f"  Q: {exchange['question']}")
                            print(f"  A: {exchange['answer'][:100]}...")
                            if len(exchange['answer']) > 100:
                                print("     (더 많은 내용 생략)")
                    else:
                        print("📝 대화 기록이 없습니다.")
                
                elif menu_choice == '3':
                    # 대화 기록 초기화
                    rag_manager.clear_history()
                    print("🗑️ 대화 기록이 초기화되었습니다.")
                
                elif menu_choice == '4':
                    # 쿼리 최적화 토글
                    rag_manager.toggle_query_optimization()
                    print("🔧 쿼리 최적화 설정이 변경되었습니다.")
                
                elif menu_choice == '5':
                    # 시스템 상태 확인
                    status = rag_manager.get_system_status()
                    print(f"\n📊 시스템 상태:")
                    print(f"  📊 임베딩 모델: {status['embedding_model']}")
                    print(f"  🔧 쿼리 최적화: {'✅' if status['query_optimization'] else '❌'}")
                    print(f"  💾 데이터베이스: {'✅' if status['database_loaded'] else '❌'}")
                    print(f"  🤖 LLM: {'✅' if status['llm_loaded'] else '❌'}")
                    print(f"  📝 대화 기록: {status['history_count']}개")
                    print(f"  🔄 히스토리 활성화: {'✅' if status['history_enabled'] else '❌'}")
                
                elif menu_choice == '6':
                    # 데이터베이스 관리
                    print("\n💾 데이터베이스 관리 메뉴:")
                    print("=" * 40)
                    
                    # 현재 DB 상태 확인
                    current_embedding_choice = db_status['embedding_choice']
                    current_db_status = check_database_status(current_embedding_choice)
                    
                    if current_db_status['exists']:
                        db_mgmt_choice = get_user_choice(
                            "💾 데이터베이스 관리 작업:",
                            [
                                "📊 데이터베이스 상세 정보 보기",
                                "💿 데이터베이스 백업하기",
                                "🔄 데이터베이스 재생성 (삭제 후 생성)",
                                "🗑️ 데이터베이스 삭제하기",
                                "🔙 메인 메뉴로 돌아가기"
                            ]
                        )
                        
                        db_manager = current_db_status['db_manager']
                        
                        if db_mgmt_choice == '1':
                            # 상세 정보 보기
                            print(f"\n📊 데이터베이스 상세 정보:")
                            print(f"  📂 경로: {current_db_status['path']}")
                            print(f"  📊 크기: {current_db_status['size_mb']} MB")
                            print(f"  📄 파일 수: {current_db_status['file_count']}개")
                            
                            # 컬렉션 정보도 시도
                            try:
                                # 임베딩 로드하여 DB 접근 시도
                                temp_embedding = EmbeddingManager.create_embedding(current_embedding_choice)
                                temp_db = db_manager.create_database(temp_embedding)
                                collection_count = temp_db._collection.count()
                                print(f"  📚 저장된 문서 청크: {collection_count}개")
                            except Exception as e:
                                print(f"  📚 저장된 문서 청크: 확인 불가 ({str(e)[:50]}...)")
                                
                        elif db_mgmt_choice == '2':
                            # 백업
                            print("💿 데이터베이스 백업을 시작합니다...")
                            if db_manager.backup_database():
                                print("✅ 백업이 완료되었습니다!")
                            else:
                                print("❌ 백업에 실패했습니다.")
                                
                        elif db_mgmt_choice == '3':
                            # 재생성
                            confirm = input("⚠️ 데이터베이스를 삭제하고 재생성하시겠습니까? (yes/no): ").strip().lower()
                            if confirm in ['yes', 'y']:
                                print("🔄 데이터베이스를 재생성합니다...")
                                if db_manager.clear_database():
                                    print("✅ 기존 데이터베이스 삭제 완료")
                                    print("🔄 새 데이터베이스가 다음 질문 시 자동 생성됩니다.")
                                else:
                                    print("❌ 데이터베이스 삭제에 실패했습니다.")
                            else:
                                print("❌ 재생성이 취소되었습니다.")
                                
                        elif db_mgmt_choice == '4':
                            # 삭제
                            confirm = input("⚠️ 데이터베이스를 완전히 삭제하시겠습니까? (yes/no): ").strip().lower()
                            if confirm in ['yes', 'y']:
                                print("🗑️ 데이터베이스를 삭제합니다...")
                                if db_manager.clear_database():
                                    print("✅ 데이터베이스가 삭제되었습니다!")
                                else:
                                    print("❌ 데이터베이스 삭제에 실패했습니다.")
                            else:
                                print("❌ 삭제가 취소되었습니다.")
                                
                        elif db_mgmt_choice == '5':
                            # 메인 메뉴로
                            print("🔙 메인 메뉴로 돌아갑니다.")
                            
                    else:
                        print("📄 현재 데이터베이스가 존재하지 않습니다.")
                        create_choice = input("새 데이터베이스를 생성하시겠습니까? (y/n): ").strip().lower()
                        if create_choice in ['y', 'yes']:
                            print("📄 새 데이터베이스가 다음 질문 시 자동 생성됩니다.")
                        
                elif menu_choice == '7':
                    # 상세 테스트 모드 (기존 admin_cli.py 스타일)
                    print("\n🧪 상세 테스트 모드 진입")
                    print("(여러 줄 질문 가능, 'END'로 완료, 'BACK'으로 메뉴 복귀)")
                    
                    while True:
                        try:
                            print("\n질문을 입력하세요 (여러 줄 가능):")
                            query_lines = []
                            line_count = 0
                            
                            while True:
                                line_count += 1
                                line = input(f"[{line_count}]> ").strip()
                                
                                if line.lower() == 'end':
                                    break
                                elif line.lower() == 'back':
                                    print("🔙 메인 메뉴로 돌아갑니다.")
                                    break
                                elif line.lower() in ['quit', 'exit']:
                                    print("\n👋 프로그램을 종료합니다.")
                                    return
                                else:
                                    query_lines.append(line)
                            
                            if line.lower() == 'back':
                                break
                            
                            if not query_lines:
                                continue
                            
                            # 질문 결합 및 처리
                            query = " ".join(query_lines).strip()
                            if query:
                                print(f"\n📝 결합된 질문: {query}")
                                print("🔍 상세 처리 중...")
                                
                                result = rag_manager.process_query(query)
                                
                                # 상세 결과 출력
                                print("\n" + "=" * 60)
                                print("📊 상세 처리 결과:")
                                print("=" * 60)
                                
                                if result["success"]:
                                    print(f"✅ 최종 답변:")
                                    print(result["answer"])
                                    
                                    if result.get("retrieved_docs"):
                                        print(f"\n📚 검색된 문서 ({len(result['retrieved_docs'])}개):")
                                        for i, doc in enumerate(result["retrieved_docs"], 1):
                                            print(f"\n📄 문서 {i}:")
                                            print(f"   내용: {doc.page_content[:200]}...")
                                            if hasattr(doc, 'metadata'):
                                                print(f"   메타데이터: {doc.metadata}")
                                else:
                                    print(f"❌ 오류: {result['answer']}")
                                
                                print("=" * 60)
                        
                        except KeyboardInterrupt:
                            print("\n🔙 메인 메뉴로 돌아갑니다.")
                            break
                
                elif menu_choice == '8':
                    print("\n👋 관리자 CLI를 종료합니다.")
                    break
                
                else:
                    print("❌ 1-8 중에서 선택하세요.")
            
            except KeyboardInterrupt:
                print("\n👋 관리자 CLI를 종료합니다.")
                break
    
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        print("   API 키나 시스템 설정을 확인하세요.")

if __name__ == "__main__":
    main()