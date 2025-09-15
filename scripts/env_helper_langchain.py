#!/usr/bin/env python3
"""
Environment Helper for LangChain Integration
Helps diagnose and fix environment issues
"""

import os
import subprocess
import sys
from pathlib import Path
from dotenv import load_dotenv

def check_dependencies():
    """Check if required dependencies are installed"""
    print("=== Checking Dependencies ===")

    required_packages = [
        "langchain",
        "langchain-community",
        "transformers",
        "torch",
        "accelerate",
        "tokenizers"
    ]

    missing = []

    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✓ {package} installed")
        except ImportError:
            print(f"✗ {package} missing")
            missing.append(package)

    if missing:
        print(f"\nTo install missing packages:")
        print(f"pip install {' '.join(missing)}")
        return False

    return True

def check_huggingface_auth():
    """Check Hugging Face authentication"""
    print("\n=== Checking Hugging Face Authentication ===")

    token = os.getenv("HUGGINGFACE_TOKEN") or os.getenv("HUGGING_FACE_HUB_TOKEN")

    if not token or token.startswith("your_"):
        print("✗ Hugging Face token not configured")
        print("Set HUGGINGFACE_TOKEN in your .env file")
        return False

    try:
        from huggingface_hub import whoami
        user_info = whoami(token)
        print(f"✓ Authenticated as: {user_info['name']}")
        return True
    except Exception as e:
        print(f"✗ Authentication failed: {e}")
        return False

def install_dependencies():
    """Install required dependencies"""
    print("\n=== Installing Dependencies ===")

    packages = [
        "langchain>=0.1.0",
        "langchain-community>=0.0.10",
        "transformers>=4.20.0",
        "torch>=1.12.0",
        "accelerate>=0.20.0",
        "tokenizers>=0.13.0",
        "huggingface_hub>=0.15.0"
    ]

    for package in packages:
        try:
            print(f"Installing {package}...")
            subprocess.run([
                sys.executable, "-m", "pip", "install", package
            ], check=True, capture_output=True, text=True)
            print(f"✓ Installed {package}")
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to install {package}: {e}")

def main():
    """Main helper function"""
    load_dotenv()

    print("=== LangChain Integration Environment Helper ===\n")

    # Check current status
    deps_ok = check_dependencies()
    auth_ok = check_huggingface_auth()

    if not deps_ok:
        install_deps = input("\nInstall missing dependencies? (y/N): ")
        if install_deps.lower() == 'y':
            install_dependencies()

    if not auth_ok:
        print("\nPlease configure your Hugging Face token:")
        print("1. Get token from https://huggingface.co/settings/tokens")
        print("2. Add to .env file: HUGGINGFACE_TOKEN=your_actual_token_here")

    if deps_ok and auth_ok:
        print("\n🎉 Environment is ready for LangChain integration!")
    else:
        print("\n⚠ Please fix the issues above before proceeding.")

if __name__ == "__main__":
    main()
