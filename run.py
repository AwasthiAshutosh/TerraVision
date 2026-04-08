"""
Forest observation and analysis system — Launcher

Convenience script to start both the FastAPI backend and
Streamlit frontend with a single command.

Usage:
    python run.py              # Start both backend and frontend
    python run.py --backend    # Start only the backend
    python run.py --frontend   # Start only the frontend
"""

import argparse
import subprocess
import sys
import time
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent


def start_backend():
    """Start the FastAPI backend server."""
    print("🚀 Starting FastAPI backend...")
    print("   URL: http://127.0.0.1:8000")
    print("   Docs: http://127.0.0.1:8000/docs")
    print()

    subprocess.run(
        [
            sys.executable, "-m", "uvicorn",
            "backend.app:app",
            "--host", "127.0.0.1",
            "--port", "8000",
            "--reload",
        ],
        cwd=str(PROJECT_ROOT),
    )


def start_frontend():
    """Start the Streamlit frontend."""
    print("🌳 Starting Streamlit frontend...")
    print("   URL: http://127.0.0.1:8501")
    print()

    subprocess.run(
        [
            sys.executable, "-m", "streamlit", "run",
            "frontend/streamlit_app.py",
            "--server.port", "8501",
            "--server.headless", "true",
            "--browser.gatherUsageStats", "false",
        ],
        cwd=str(PROJECT_ROOT),
    )


def start_both():
    """Start both backend and frontend in subprocesses."""
    print("=" * 60)
    print("🌳 Forest observation and analysis system")
    print("=" * 60)
    print()

    # Start backend in background
    backend_proc = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn",
            "backend.app:app",
            "--host", "127.0.0.1",
            "--port", "8000",
            "--reload",
        ],
        cwd=str(PROJECT_ROOT),
    )

    # Wait for backend to start
    time.sleep(3)

    # Start frontend
    frontend_proc = subprocess.Popen(
        [
            sys.executable, "-m", "streamlit", "run",
            "frontend/streamlit_app.py",
            "--server.port", "8501",
            "--server.headless", "true",
            "--browser.gatherUsageStats", "false",
        ],
        cwd=str(PROJECT_ROOT),
    )

    print()
    print("✅ System Running!")
    print("   Backend:  http://127.0.0.1:8000 (API docs: /docs)")
    print("   Frontend: http://127.0.0.1:8501")
    print()
    print("Press Ctrl+C to stop both servers.")
    print()

    try:
        # Poll both processes — if either exits, shut down the other
        while True:
            if backend_proc.poll() is not None:
                print("\n⚠ Backend process exited (code: %d)" % backend_proc.returncode)
                frontend_proc.terminate()
                frontend_proc.wait()
                break
            if frontend_proc.poll() is not None:
                print("\n⚠ Frontend process exited (code: %d)" % frontend_proc.returncode)
                backend_proc.terminate()
                backend_proc.wait()
                break
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        backend_proc.terminate()
        frontend_proc.terminate()
        backend_proc.wait()
        frontend_proc.wait()
        print("✓ Servers stopped.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Forest observation and analysis system Launcher",
    )
    parser.add_argument("--backend", action="store_true", help="Start only the backend")
    parser.add_argument("--frontend", action="store_true", help="Start only the frontend")

    args = parser.parse_args()

    if args.backend:
        start_backend()
    elif args.frontend:
        start_frontend()
    else:
        start_both()
