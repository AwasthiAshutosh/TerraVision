"""
Forest observation and analysis system — Launcher

Convenience script to start both the FastAPI backend and
Streamlit frontend with a single command.

Usage:
    python run.py              # Start both backend and frontend
    python run.py --backend    # Start only the backend
    python run.py --frontend   # Start only the frontend
    python run.py --train      # Train the ML model
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
        backend_proc.wait()
        frontend_proc.wait()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        backend_proc.terminate()
        frontend_proc.terminate()
        backend_proc.wait()
        frontend_proc.wait()
        print("✓ Servers stopped.")


def train_model():
    """Train the ML classification model."""
    print("🤖 Training Random Forest classifier...")
    print()

    # Add project root to path
    sys.path.insert(0, str(PROJECT_ROOT))

    from ml.training.train_rf import train_random_forest
    report = train_random_forest()

    print()
    print("=" * 50)
    print(f"✅ Training complete!")
    print(f"   Accuracy: {report['performance']['test_accuracy']:.4f}")
    print(f"   CV Score: {report['performance']['cv_accuracy_mean']:.4f} ± {report['performance']['cv_accuracy_std']:.4f}")
    print(f"   Model saved to: ml/models/random_forest_model.joblib")
    print("=" * 50)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Forest observation and analysis system Launcher",
    )
    parser.add_argument("--backend", action="store_true", help="Start only the backend")
    parser.add_argument("--frontend", action="store_true", help="Start only the frontend")
    parser.add_argument("--train", action="store_true", help="Train ML model")

    args = parser.parse_args()

    if args.backend:
        start_backend()
    elif args.frontend:
        start_frontend()
    elif args.train:
        train_model()
    else:
        start_both()
