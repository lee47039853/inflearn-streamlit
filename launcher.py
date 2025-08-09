#!/usr/bin/env python3
"""
소득세 챗봇 통합 런처
사용자와 관리자 모드를 선택하여 실행할 수 있습니다.
"""

import subprocess
import sys
import os
import argparse

def check_dependencies():
    """필요한 의존성 확인"""
    try:
        import streamlit
        import langchain
        import chromadb
        print("✅ 모든 의존성이 설치되어 있습니다.")
        return True
    except ImportError as e:
        print(f"❌ 필요한 의존성이 설치되지 않았습니다: {e}")
        print("다음 명령어로 의존성을 설치하세요:")
        print("pip install -r requirements.txt")
        return False

def run_user_mode():
    """일반 사용자 모드 실행"""
    print("👤 일반 사용자 모드를 시작합니다...")
    print("📱 간단하고 안전한 채팅 인터페이스")
    print("🌐 브라우저에서 http://localhost:8501 을 열어주세요.")
    print("⏹️  종료하려면 Ctrl+C를 누르세요.")
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
    except KeyboardInterrupt:
        print("\n👋 일반 사용자 모드를 종료합니다.")
    except Exception as e:
        print(f"❌ 일반 사용자 모드 실행 중 오류 발생: {e}")
        sys.exit(1)

def run_admin_mode():
    """관리자 모드 실행"""
    print("🛠️  관리자 모드를 시작합니다...")
    print("⚠️  주의: 이 화면은 시스템 관리자 전용입니다.")
    
    # 관리자 확인
    if not os.getenv('ADMIN_MODE'):
        response = input("관리자 모드를 실행하시겠습니까? (y/N): ")
        if response.lower() not in ['y', 'yes']:
            print("❌ 관리자 모드 실행이 취소되었습니다.")
            return
    
    print("🚀 관리자 대시보드를 시작합니다...")
    print("🌐 브라우저에서 http://localhost:8502 를 열어주세요.")
    print("⏹️  종료하려면 Ctrl+C를 누르세요.")
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "admin.py",
            "--server.port", "8502",
            "--server.address", "localhost"
        ])
    except KeyboardInterrupt:
        print("\n👋 관리자 모드를 종료합니다.")
    except Exception as e:
        print(f"❌ 관리자 모드 실행 중 오류 발생: {e}")
        sys.exit(1)

def run_both_modes():
    """사용자와 관리자 모드 동시 실행"""
    print("🚀 사용자 + 관리자 모드를 동시에 시작합니다...")
    print("👤 사용자 모드: http://localhost:8501")
    print("🛠️  관리자 모드: http://localhost:8502")
    print("⏹️  종료하려면 Ctrl+C를 누르세요.")
    
    try:
        # 사용자 모드 백그라운드 실행
        user_process = subprocess.Popen([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
        
        # 관리자 모드 포그라운드 실행
        admin_process = subprocess.Popen([
            sys.executable, "-m", "streamlit", "run", "admin.py",
            "--server.port", "8502",
            "--server.address", "localhost"
        ])
        
        # 두 프로세스가 종료될 때까지 대기
        user_process.wait()
        admin_process.wait()
        
    except KeyboardInterrupt:
        print("\n👋 모든 서비스를 종료합니다...")
        try:
            user_process.terminate()
            admin_process.terminate()
        except:
            pass
    except Exception as e:
        print(f"❌ 동시 실행 중 오류 발생: {e}")
        sys.exit(1)

def interactive_mode():
    """대화형 모드 선택"""
    print("🚀 소득세 챗봇 시스템")
    print("=" * 50)
    print("실행할 모드를 선택하세요:")
    print("1. 👤 일반 사용자 모드 (포트 8501)")
    print("2. 🛠️  관리자 모드 (포트 8502)")
    print("3. 🔄 두 모드 동시 실행")
    print("4. ❌ 종료")
    print("=" * 50)
    
    while True:
        try:
            choice = input("선택 (1-4): ").strip()
            
            if choice == '1':
                run_user_mode()
                break
            elif choice == '2':
                run_admin_mode()
                break
            elif choice == '3':
                run_both_modes()
                break
            elif choice == '4':
                print("👋 런처를 종료합니다.")
                break
            else:
                print("❌ 잘못된 선택입니다. 1-4 중에서 선택해주세요.")
        except KeyboardInterrupt:
            print("\n👋 런처를 종료합니다.")
            break

def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description='소득세 챗봇 통합 런처')
    parser.add_argument('mode', nargs='?', choices=['user', 'admin', 'both'], 
                       help='실행 모드 선택: user(일반), admin(관리자), both(동시)')
    parser.add_argument('--no-check', action='store_true', 
                       help='의존성 검사 건너뛰기')
    
    args = parser.parse_args()
    
    # 의존성 확인
    if not args.no_check and not check_dependencies():
        sys.exit(1)
    
    # 모드에 따른 실행
    if args.mode == 'user':
        run_user_mode()
    elif args.mode == 'admin':
        run_admin_mode()
    elif args.mode == 'both':
        run_both_modes()
    else:
        # 인수가 없으면 대화형 모드
        interactive_mode()

if __name__ == "__main__":
    main()
