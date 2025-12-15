#!/usr/bin/env python3
"""
Upload Environment Variables to HuggingFace Space Secrets

This script uploads specific environment variables to a HuggingFace Space.
Requires: pip install huggingface_hub python-dotenv
"""

import os
import sys
from pathlib import Path

# New variables to upload for 2025 upgrades
NEW_ENV_VARS = [
    # WeKnora settings
    "ENABLE_WEKNORA",
    "MAX_UPLOAD_SIZE",
    
    # VibeVoice settings
    "ENABLE_VIBEVOICE",
    "VIBEVOICE_MODEL_PATH",
    
    
    # RAG settings
    "USE_RERANKING",
    "USE_HYDE",
    "RAG_TOP_K",
    
    
]


def main():
    # Check if huggingface_hub is installed
    try:
        from huggingface_hub import HfApi
    except ImportError:
        print("Installing huggingface_hub...")
        os.system(f"{sys.executable} -m pip install huggingface_hub python-dotenv")
        from huggingface_hub import HfApi
    
    from dotenv import load_dotenv
    
    # Load .env file
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✓ Loaded .env from {env_path}")
    else:
        print(f"⚠ No .env file found at {env_path}")
    
    # Get HuggingFace token
    hf_token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN")
    if not hf_token:
        hf_token = input("Enter your HuggingFace token: ").strip()
    
    if not hf_token:
        print("✗ HuggingFace token is required")
        return 1
    
    # Get space name
    space_name = os.getenv("HF_SPACE_NAME") or os.getenv("SPACE_ID")
    if not space_name:
        space_name = input("Enter your HuggingFace Space name (e.g., username/space-name): ").strip()
    
    if not space_name:
        print("✗ Space name is required")
        return 1
    
    # Initialize API
    api = HfApi(token=hf_token)
    
    print(f"\n📦 Uploading secrets to {space_name}...")
    print("=" * 50)
    
    uploaded = 0
    skipped = 0
    
    for var_name in NEW_ENV_VARS:
        value = os.getenv(var_name)
        
        if not value:
            print(f"⏭  {var_name}: Not set, skipping")
            skipped += 1
            continue
        
        try:
            api.add_space_secret(
                repo_id=space_name,
                key=var_name,
                value=value,
            )
            # Mask sensitive values in output
            display_value = value[:4] + "***" if len(value) > 4 else "***"
            print(f"✓  {var_name}: {display_value}")
            uploaded += 1
        except Exception as e:
            print(f"✗  {var_name}: Failed - {e}")
    
    print("=" * 50)
    print(f"\n✅ Uploaded: {uploaded} | ⏭ Skipped: {skipped}")
    
    if uploaded > 0:
        print(f"\n🚀 Secrets uploaded to https://huggingface.co/spaces/{space_name}")
        print("   The space will restart automatically to apply changes.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
