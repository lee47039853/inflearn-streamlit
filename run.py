#!/usr/bin/env python3
"""
소득세 챗봇 실행 스크립트
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

def main():
    """메인 실행 함수"""
    print("🚀 소득세 챗봇을 시작합니다...")
    
    # 의존성 확인
    if not check_dependencies():
        sys.exit(1)
    
    # Streamlit 애플리케이션 실행
    try:
        print("📱 Streamlit 애플리케이션을 시작합니다...")
        print("🌐 브라우저에서 http://localhost:8501 을 열어주세요.")
        print("⏹️  종료하려면 Ctrl+C를 누르세요.")
        
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "chat.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
        
    except KeyboardInterrupt:
        print("\n👋 애플리케이션을 종료합니다.")
    except Exception as e:
        print(f"❌ 애플리케이션 실행 중 오류 발생: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 