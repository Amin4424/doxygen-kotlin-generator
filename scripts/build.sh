#!/usr/bin/env bash
set -e

# Resolve directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo "=== Kotlin Doxygen Build Script (Unix) ==="

VENV_DIR="$PROJECT_ROOT/venv"
PYTHON_EXE="$VENV_DIR/bin/python"
PIP_EXE="$VENV_DIR/bin/pip"
PYINSTALLER_EXE="$VENV_DIR/bin/pyinstaller"

# 1. Setup virtual environment if not exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating Python virtual environment in 'venv'..."
    python3 -m venv venv
fi

# 2. Upgrade pip and install development dependencies
echo "Installing/updating dependencies in virtual environment..."
$PYTHON_EXE -m pip install --upgrade pip
$PIP_EXE install -e .[dev]

# 3. Run tests
echo "Running tests..."
$PYTHON_EXE -m unittest discover -s tests

# 4. Build executable using PyInstaller
echo "Building standalone executable using PyInstaller..."
$PYINSTALLER_EXE --onefile --clean --name kotlin-doxygen kotlin_doxygen/__main__.py

# 5. Verify and output
EXE_PATH="$PROJECT_ROOT/dist/kotlin-doxygen"
if [ -f "$EXE_PATH" ]; then
    echo -e "\nSuccess! Executable successfully generated at:"
    echo "$EXE_PATH"
else
    echo "Build failed: Executable not found at $EXE_PATH"
    exit 1
fi
