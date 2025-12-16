#!/usr/bin/env python3
"""
Upload Environment Variables to HuggingFace Space Secrets

This script uploads ALL environment variables from .env file to a HuggingFace Space.
Requires: pip install huggingface_hub python-dotenv
"""

import os
import sys
import re
from pathlib import Path


def parse_env_file(env_path: Path) -> dict[str, str]:
    """Parse .env file and return all key-value pairs."""
    env_vars = {}
    
    if not env_path.exists():
        return env_vars
    
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Match KEY=VALUE pattern (handles quoted values)
            match = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$', line)
            if match:
                key = match.group(1)
                value = match.group(2)
                
                # Remove surrounding quotes if present
                if (value.startswith('"') and value.endswith('"')) or \
                   (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]
                
                env_vars[key] = value
    
    return env_vars


def main():
    # Check if huggingface_hub is installed
    try:
        from huggingface_hub import HfApi
    except ImportError:
        print("Installing huggingface_hub...")
        os.system(f"{sys.executable} -m pip install huggingface_hub python-dotenv")
        from huggingface_hub import HfApi
    
    from dotenv import load_dotenv
    
    # Load .env file for getting HF credentials
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✓ Found .env at {env_path}")
    else:
        print(f"✗ No .env file found at {env_path}")
        return 1
    
    # Parse entire .env file
    env_vars = parse_env_file(env_path)
    print(f"✓ Parsed {len(env_vars)} environment variables from .env")
    
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
    
    # Variables to exclude from upload (sensitive local-only vars)
    EXCLUDE_VARS = {
        "HF_TOKEN",
        "HUGGINGFACE_TOKEN", 
        "HF_SPACE_NAME",
        "SPACE_ID",
    }
    
    # Initialize API
    api = HfApi(token=hf_token)
    
    print(f"\n📦 Uploading ALL secrets from .env to {space_name}...")
    print("=" * 60)
    
    uploaded = 0
    skipped = 0
    failed = 0
    
    for var_name, value in env_vars.items():
        # Skip excluded variables
        if var_name in EXCLUDE_VARS:
            print(f"⏭  {var_name}: Excluded (local-only)")
            skipped += 1
            continue
        
        # Skip empty values
        if not value:
            print(f"⏭  {var_name}: Empty value, skipping")
            skipped += 1
            continue
        
        try:
            api.add_space_secret(
                repo_id=space_name,
                key=var_name,
                value=value,
            )
            # Mask sensitive values in output
            if any(s in var_name.upper() for s in ['KEY', 'SECRET', 'TOKEN', 'PASSWORD', 'API']):
                display_value = value[:4] + "***" if len(value) > 4 else "***"
            else:
                display_value = value[:30] + "..." if len(value) > 30 else value
            print(f"✓  {var_name}: {display_value}")
            uploaded += 1
        except Exception as e:
            print(f"✗  {var_name}: Failed - {e}")
            failed += 1
    
    print("=" * 60)
    print(f"\n✅ Uploaded: {uploaded} | ⏭ Skipped: {skipped} | ✗ Failed: {failed}")
    
    if uploaded > 0:
        print(f"\n🚀 Secrets uploaded to https://huggingface.co/spaces/{space_name}")
        print("   The space will restart automatically to apply changes.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
