"""
Top-Level Launcher for Gaussian Filter Web Interface
====================================================
Course: CS-305 Computer Vision Case Study
Run with:
    python app.py
or
    python web/server.py
"""

import sys
import os
from pathlib import Path

# Add project root and src to path
ROOT_DIR = Path(__file__).resolve().parent
if (ROOT_DIR / "gaussian_filter_project").exists():
    PROJECT_DIR = ROOT_DIR / "gaussian_filter_project"
else:
    PROJECT_DIR = ROOT_DIR
WEB_DIR = PROJECT_DIR / "web"
SRC_DIR = PROJECT_DIR / "src"

sys.path.insert(0, str(SRC_DIR))
sys.path.insert(0, str(WEB_DIR))

if __name__ == "__main__":
    from server import run_server
    import argparse

    parser = argparse.ArgumentParser(description="Launch CS-305 Gaussian Filter Web UI")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host IP (default: 127.0.0.1)")
    args = parser.parse_args()

    run_server(port=args.port, host=args.host)
