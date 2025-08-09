#!/usr/bin/env python3
"""
소득세 챗봇 관리자 실행 스크립트
"""

import subprocess
import sys
import os

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

def check_admin_access():
    """관리자 접근 권한 확인"""
    print("🛠️  관리자 화면을 시작합니다...")
    print("⚠️  주의: 이 화면은 시스템 관리자 전용입니다.")
    
    # 간단한 확인 (실제 환경에서는 더 강력한 인증 필요)
    if not os.getenv('ADMIN_MODE'):
        response = input("관리자 화면을 실행하시겠습니까? (y/N): ")
        if response.lower() not in ['y', 'yes']:
            print("❌ 관리자 화면 실행이 취소되었습니다.")
            return False
    
    return True

def main():
    """메인 실행 함수"""
    print("🛠️  소득세 챗봇 관리자 시스템을 시작합니다...")
    
    # 의존성 확인
    if not check_dependencies():
        sys.exit(1)
    
    # 관리자 접근 확인
    if not check_admin_access():
        sys.exit(1)
    
    # Streamlit 관리자 애플리케이션 실행
    try:
        print("🚀 관리자 대시보드를 시작합니다...")
        print("🌐 브라우저에서 http://localhost:8502 를 열어주세요.")
        print("⚠️  일반 사용자는 http://localhost:8501 을 이용하세요.")
        print("⏹️  종료하려면 Ctrl+C를 누르세요.")
        
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "admin.py",
            "--server.port", "8502",
            "--server.address", "localhost",
            "--server.headless", "true",
            "--browser.serverAddress", "localhost"
        ])
        
    except KeyboardInterrupt:
        print("\n👋 관리자 시스템을 종료합니다.")
    except Exception as e:
        print(f"❌ 관리자 시스템 실행 중 오류 발생: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
