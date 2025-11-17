#!/usr/bin/env python3
"""
Refresh Data Pipeline - Run spiders, parse data, and repopulate databases

This script runs the complete data refresh pipeline:
1. Crawl data using all spiders
2. Process and parse the crawled data
3. Populate vector databases with processed chunks
"""

import sys
import os
import subprocess
from pathlib import Path
from loguru import logger

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def get_venv_python():
    """Get the Python interpreter from virtual environment if it exists"""
    # Check for common venv locations
    venv_paths = [
        project_root / "venv",
        project_root / ".venv",
        project_root / "env",
    ]
    
    for venv_path in venv_paths:
        if venv_path.exists():
            # Windows
            python_exe = venv_path / "Scripts" / "python.exe"
            if python_exe.exists():
                return str(python_exe)
            
            # Unix/Mac
            python_exe = venv_path / "bin" / "python"
            if python_exe.exists():
                return str(python_exe)
    
    # Check if we're already in a venv
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        # We're in a venv, use current Python
        return sys.executable
    
    # No venv found, use current Python
    return sys.executable

def run_command(module_path, description, python_exe):
    """Run a Python module and return success status"""
    print("\n" + "=" * 60)
    print(f"🔄 {description}")
    print("=" * 60)
    
    try:
        result = subprocess.run(
            [python_exe, "-m", module_path],
            cwd=project_root,
            check=True
        )
        print(f"✔ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed with exit code {e.returncode}")
        logger.error(f"Error running {module_path}: {e}")
        return False
    except KeyboardInterrupt:
        print(f"\n⚠️  {description} interrupted by user")
        return False

def main():
    """Run the complete data refresh pipeline"""
    print("=" * 60)
    print("🚀 AmaniQuery Data Refresh Pipeline")
    print("=" * 60)
    
    # Detect and use virtual environment
    python_exe = get_venv_python()
    venv_name = Path(python_exe).parent.parent.name if "venv" in python_exe or ".venv" in python_exe or "env" in python_exe else "system"
    
    print(f"\n🐍 Python interpreter: {python_exe}")
    if venv_name != "system":
        print(f"✔Using virtual environment: {venv_name}")
    else:
        print("⚠️  No virtual environment detected - using system Python")
        print("   Consider activating venv first:")
        print("   Windows: venv\\Scripts\\activate")
        print("   Linux/Mac: source venv/bin/activate")
    
    print("\nThis will:")
    print("  1. Run all spiders to crawl fresh data")
    print("  2. Process and parse the crawled data")
    print("  3. Populate vector databases with processed chunks")
    print("\n⚠️  This may take 1-3 hours depending on data volume")
    
    response = input("\nContinue? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled.")
        return 0
    
    # Step 1: Crawl data
    if not run_command("Module1_NiruSpider.crawl_all", "Step 1: Crawling Data", python_exe):
        print("\n✗ Crawling failed. Stopping pipeline.")
        return 1
    
    # Step 2: Process data
    if not run_command("Module2_NiruParser.process_all", "Step 2: Processing Data", python_exe):
        print("\n✗ Processing failed. Stopping pipeline.")
        return 1
    
    # Step 3: Populate vector databases
    if not run_command("Module3_NiruDB.populate_db", "Step 3: Populating Vector Databases", python_exe):
        print("\n✗ Database population failed.")
        return 1
    
    print("\n" + "=" * 60)
    print("🎉 Data Refresh Complete!")
    print("=" * 60)
    print("\n✔ All steps completed successfully")
    print("📊 Your databases are now populated with fresh data")
    print("\nYou can now start the API server:")
    print("   python start_api.py")
    print("=" * 60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

