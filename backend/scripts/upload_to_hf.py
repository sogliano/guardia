
import os
import sys
from pathlib import Path
from huggingface_hub import HfApi, login

def upload_model():
    print("🚀 Guard-IA Model Uploader")
    print("==========================")
    
    # Check for model files
    base_path = Path(__file__).parent.parent
    model_path = base_path / "ml_models" / "distilbert-guardia"
    
    if not model_path.exists():
        print(f"❌ Error: Model directory not found at {model_path}")
        return

    # Check login
    try:
        api = HfApi()
        user = api.whoami()
        print(f"✅ Logged in as: {user['name']}")
    except:
        print("⚠️  You are not logged in to Hugging Face.")
        token = input("👉 Paste your Hugging Face Write Token: ").strip()
        if not token:
            print("❌ Token required.")
            return
        login(token)
        api = HfApi()
        user = api.whoami()

    # Get Repo Name
    print(f"\n📦 Local model found: {model_path}")
    default_repo = f"{user['name']}/distilbert-guardia-v2"
    repo_id = input(f"👉 Enter Hub Repository ID [{default_repo}]: ").strip() or default_repo
    
    # Create repo if not exists
    try:
        api.create_repo(repo_id, exist_ok=True)
        print(f"✅ Repository {repo_id} ready.")
    except Exception as e:
        print(f"❌ Error creating repo: {e}")
        return

    # Upload
    print(f"\n⬆️  Uploading model to {repo_id}...")
    try:
        api.upload_folder(
            folder_path=str(model_path),
            repo_id=repo_id,
            repo_type="model"
        )
        print("\n✅ Upload Complete! 🎉")
        print("\nNext steps:")
        print(f"1. Set this environment variable in your production deployment:")
        print(f"   ML_MODEL_HF_REPO={repo_id}")
    except Exception as e:
        print(f"❌ Upload failed: {e}")

if __name__ == "__main__":
    upload_model()
