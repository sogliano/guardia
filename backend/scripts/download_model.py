#!/usr/bin/env python3
"""
Download ML model from Hugging Face Hub (with authentication support).
Usage: python scripts/download_model.py [--repo REPO_ID] [--dest DEST_DIR]
Env: HF_TOKEN (optional, for private repos)
"""

import os
import argparse
from pathlib import Path
import structlog
from huggingface_hub import snapshot_download

# Configure logger
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ]
)
logger = structlog.get_logger()

# Default config
DEFAULT_REPO = "Rodrigo-Miranda-0/distilbert-guardia-v2"
DEFAULT_DEST = "backend/ml_models/distilbert-guardia"


def download_model(repo_id: str, dest_dir: Path, token: str | None = None) -> None:
    """Download model snapshot from HF Hub."""
    logger.info("download_started", repo=repo_id, dest=str(dest_dir))
    
    try:
        # snapshot_download handles auth via token arg or HF_TOKEN env var
        snapshot_download(
            repo_id=repo_id,
            local_dir=dest_dir,
            local_dir_use_symlinks=False,  # Important for Docker COPY
            token=token,
            ignore_patterns=["*.msgpack", "*.h5", ".git*"], # Skip unnecessary files
        )
        logger.info("download_complete", path=str(dest_dir))
    except Exception as e:
        logger.error("download_failed", error=str(e))
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download Guard-IA ML Model")
    parser.add_argument("--repo", default=DEFAULT_REPO, help="Hugging Face Repo ID")
    parser.add_argument("--dest", default=DEFAULT_DEST, help="Destination directory (relative to backend root)")
    args = parser.parse_args()

    # Ensure destination exists
    dest_path = Path(args.dest).resolve()
    dest_path.mkdir(parents=True, exist_ok=True)

    # Get token from env if not provided
    token = os.getenv("HF_TOKEN")
    if not token:
        logger.warning("no_hf_token_found", msg="Attempting public download. For private repos, set HF_TOKEN env var.")

    download_model(args.repo, dest_path, token)
