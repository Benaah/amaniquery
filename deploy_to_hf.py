#!/usr/bin/env python3
"""
Deploy AmaniQuery to Hugging Face Space

Simplified deployment script that uses the standard Dockerfile.
This script uploads only necessary code files, excluding build artifacts.

Usage:
    python deploy_to_hf.py [--space-id Benaah/amaniquery]
"""

import os
import shutil
import argparse
from pathlib import Path
from typing import List
from huggingface_hub import HfApi, login
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
SPACE_ID = "Benaah/amaniquery"
TEMP_DIR = Path(".hf-deploy-temp")

# Binary file extensions to exclude
BINARY_EXTENSIONS = {'.png', '.ico', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.bin', '.pt', '.pth'}
# Directories to exclude
EXCLUDE_DIRS = {
    '.git', '.git-rewrite', '__pycache__', 'node_modules', 'venv', 'env', 
    '.venv', 'dist', 'build', '.pytest_cache', 'htmlcov', '.coverage',
    'embeddings', 'processed', 'raw', 'models', 'logs', 'output',
    'imgs',  # Exclude images directory
    'frontend',  # Exclude frontend - deployed separately
    'android-app',  # Exclude Android app - deployed separately
    '.scrapy', 'httpcache',  # Exclude Scrapy cache
    '.hf-deploy-temp',  # Exclude temp directory itself
    'WeKnora/dataset', # Weknora Dataset examples
}

# Files to exclude
EXCLUDE_FILES = {
    '.DS_Store', 'Thumbs.db', '*.pyc', '*.pyo', '*.pyd'
}


def should_exclude(path: Path) -> bool:
    """Check if a file or directory should be excluded."""
    # Always allow files in chroma_db, bypassing other checks
    if 'chroma_db' in path.parts:
        return False

    # Check if it's in an excluded directory
    parts = path.parts
    for part in parts:
        if part in EXCLUDE_DIRS:
            return True
    
    # Check file extension
    if path.is_file() and path.suffix.lower() in BINARY_EXTENSIONS:
        return True
    
    # Check excluded files
    if path.is_file() and path.name in EXCLUDE_FILES:
        return True
    
    return False


def collect_code_files(source_dir: Path, dest_dir: Path) -> List[Path]:
    """Collect all code files from source directory, excluding binary files."""
    code_files = []
    
    for root, dirs, files in os.walk(source_dir):
        # Filter out excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        root_path = Path(root)
        
        # Skip if root itself should be excluded
        if should_exclude(root_path):
            continue
        
        for file in files:
            file_path = root_path / file
            
            # Skip excluded files
            if should_exclude(file_path):
                continue
            
            # Skip hidden files except .gitignore and similar
            if file.startswith('.') and file not in {'.gitignore', '.dockerignore', '.env.example', '.nojekyll'}:
                continue
            
            code_files.append(file_path)
    
    return code_files


def copy_files_to_temp(source_dir: Path, temp_dir: Path, code_files: List[Path]):
    """Copy code files to temporary directory maintaining directory structure."""
    temp_dir.mkdir(exist_ok=True)
    
    for file_path in code_files:
        # Calculate relative path
        rel_path = file_path.relative_to(source_dir)
        dest_path = temp_dir / rel_path
        
        # Create parent directories
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy file
        try:
            shutil.copy2(file_path, dest_path)
            print(f"Copied: {rel_path}")
        except PermissionError:
            print(f"ERROR: Could not copy {rel_path}. The file might be in use (locked).")
            print("       Please STOP any running servers (start_api.py) and try again.")
            # We should probably fail hard here if it's a critical file
            if "chroma" in str(rel_path):
                raise
        except Exception as e:
            print(f"ERROR: Failed to copy {rel_path}: {e}")
            if "chroma" in str(rel_path):
                raise


def upload_to_hf_space(temp_dir: Path, space_id: str, token: str):
    """Upload files to Hugging Face Space."""
    api = HfApi(token=token)
    
    print(f"\nUploading files to {space_id}...")
    
    # Upload entire directory using upload_folder (more efficient)
    try:
        api.upload_folder(
            folder_path=str(temp_dir),
            repo_id=space_id,
            repo_type="space",
            ignore_patterns=[".git*", "__pycache__", "*.pyc", ".scrapy", "httpcache"],
        )
        print("✓ All files uploaded successfully!")
    except Exception as e:
        print(f"Error uploading folder: {e}")
        # Fallback to individual file uploads
        print("Falling back to individual file uploads...")
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                local_path = Path(root) / file
                rel_path = local_path.relative_to(temp_dir)
                hf_path = str(rel_path).replace('\\', '/')
                
                try:
                    api.upload_file(
                        path_or_fileobj=str(local_path),
                        path_in_repo=hf_path,
                        repo_id=space_id,
                        repo_type="space",
                    )
                    print(f"Uploaded: {hf_path}")
                except Exception as e2:
                    print(f"Error uploading {hf_path}: {e2}")


def main():
    """Main deployment function."""
    parser = argparse.ArgumentParser(description="Deploy AmaniQuery to HuggingFace Spaces")
    parser.add_argument("--space-id", default=SPACE_ID, help="HuggingFace Space ID (default: Benaah/amaniquery)")
    parser.add_argument("--dry-run", action="store_true", help="Collect files but don't upload")
    args = parser.parse_args()
    
    print("=" * 60)
    print("Deploying to Hugging Face Space")
    print(f"Space ID: {args.space_id}")
    print(f"Using: Dockerfile (standard)")
    print("=" * 60)
    
    # Get Hugging Face token
    token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN")
    if not token and not args.dry_run:
        print("Error: HF_TOKEN or HUGGINGFACE_TOKEN environment variable not set")
        print("Please set it with: export HF_TOKEN=your_token_here")
        return 1
    
    # Login to Hugging Face
    if not args.dry_run:
        try:
            login(token=token)
            print("✓ Logged in to Hugging Face")
        except Exception as e:
            print(f"Error logging in: {e}")
            return 1
    
    source_dir = Path(".")
    
    # Clean up temp directory if it exists
    if TEMP_DIR.exists():
        print(f"Cleaning up {TEMP_DIR}...")
        shutil.rmtree(TEMP_DIR)
    
    try:
        # Collect code files
        print("\nCollecting code files...")
        code_files = collect_code_files(source_dir, TEMP_DIR)
        print(f"Found {len(code_files)} code files to deploy")
        
        # Copy files to temp directory
        print("\nCopying files to temporary directory...")
        copy_files_to_temp(source_dir, TEMP_DIR, code_files)
        
        # Ensure Dockerfile exists
        dockerfile_src = source_dir / "Dockerfile"
        if not dockerfile_src.exists():
            print("Error: Dockerfile not found in project root")
            return 1
        
        shutil.copy2(dockerfile_src, TEMP_DIR / "Dockerfile")
        print("✓ Copied Dockerfile")
        
        # Upload to Hugging Face
        if args.dry_run:
            print("\n[DRY RUN] Files prepared but not uploaded")
            print(f"Review files in: {TEMP_DIR}")
        else:
            print("\nUploading to Hugging Face Space...")
            upload_to_hf_space(TEMP_DIR, args.space_id, token)
        
        print("\n" + "=" * 60)
        print("✓ Deployment complete!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nError during deployment: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        # Clean up temp directory
        if not args.dry_run and TEMP_DIR.exists():
            print(f"\nCleaning up {TEMP_DIR}...")
            shutil.rmtree(TEMP_DIR)
    
    return 0


if __name__ == "__main__":
    exit(main())

