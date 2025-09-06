#!/usr/bin/env python3
"""
Virtual Environment Setup Script for Plug-and-Play RAG System
=============================================================

This script sets up a Python virtual environment and installs all dependencies.
Use this for local development instead of Docker.
"""

import os
import sys
import subprocess
import venv
from pathlib import Path

def run_command(command, cwd=None):
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            check=True, 
            capture_output=True, 
            text=True,
            cwd=cwd
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running command: {command}")
        print(f"Error: {e.stderr}")
        return None

def create_virtual_environment():
    """Create a Python virtual environment."""
    venv_path = Path(".venv")
    
    if venv_path.exists():
        print("📁 Virtual environment already exists at .venv")
        return venv_path
    
    print("🔧 Creating Python virtual environment...")
    try:
        venv.create(".venv", with_pip=True)
        print("✅ Virtual environment created successfully")
        return venv_path
    except Exception as e:
        print(f"❌ Failed to create virtual environment: {e}")
        return None

def get_activation_command():
    """Get the command to activate virtual environment based on OS."""
    if os.name == 'nt':  # Windows
        return ".venv\\Scripts\\activate"
    else:  # Unix/Linux/macOS
        return "source .venv/bin/activate"

def install_dependencies(venv_path):
    """Install Python dependencies in the virtual environment."""
    print("📦 Installing Python dependencies...")
    
    # Determine Python executable in venv
    if os.name == 'nt':  # Windows
        python_exe = venv_path / "Scripts" / "python.exe"
        pip_exe = venv_path / "Scripts" / "pip.exe"
    else:  # Unix/Linux/macOS
        python_exe = venv_path / "bin" / "python"
        pip_exe = venv_path / "bin" / "pip"
    
    # Upgrade pip first
    result = run_command(f'"{pip_exe}" install --upgrade pip')
    if result is None:
        return False
    
    # Install requirements
    result = run_command(f'"{pip_exe}" install -r requirements.txt')
    if result is None:
        return False
    
    print("✅ Dependencies installed successfully")
    return True

def create_env_file():
    """Create .env file from template if it doesn't exist."""
    env_file = Path(".env")
    template_file = Path(".env.template")
    
    if env_file.exists():
        print("📄 .env file already exists")
        return
    
    if template_file.exists():
        print("📄 Creating .env file from template...")
        import shutil
        shutil.copy(template_file, env_file)
        print("✅ .env file created")
        print("⚠️  Please edit .env file and add your API keys")
    else:
        print("⚠️  No .env.template found")

def create_directories():
    """Create necessary directories."""
    directories = ["data", "logs", "chroma_db"]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    
    print("📁 Created necessary directories")

def main():
    """Main setup function."""
    print("🚀 Setting up Plug-and-Play RAG Development Environment")
    print("=" * 60)
    
    # Check Python version
    if sys.version_info < (3, 12):
        print("❌ Python 3.12+ is required")
        print(f"Current version: {sys.version}")
        sys.exit(1)
    
    print(f"✅ Python version: {sys.version}")
    
    # Create virtual environment
    venv_path = create_virtual_environment()
    if not venv_path:
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies(venv_path):
        sys.exit(1)
    
    # Create .env file
    create_env_file()
    
    # Create directories
    create_directories()
    
    # Success message
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print(f"1. Activate virtual environment: {get_activation_command()}")
    print("2. Edit .env file with your API keys")
    print("3. Add your CSV files to the data/ folder")
    print("4. Edit config/app_config.yaml if needed")
    print("5. Run the development server: python run.py")
    print("\n📚 For more help, see:")
    print("   - README.md - Project overview")
    print("   - QUICK_START_GUIDE.md - Step-by-step guide")
    print("   - GETTING_STARTED_CHECKLIST.md - Verification checklist")

if __name__ == "__main__":
    main()
