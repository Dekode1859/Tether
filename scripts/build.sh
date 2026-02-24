#!/bin/bash
# Tether Build Script
# Usage: ./scripts/build.sh

set -e

echo "Building Tether..."

# Build with PyInstaller
pyinstaller tether.spec

echo "Build complete!"
echo "Executable location: dist/Tether.exe"
