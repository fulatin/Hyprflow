#!/bin/bash

# HyperFlow Installation Script

set -e  # Exit on any error

echo "Installing HyperFlow: Hyprland Visual Automation Assistant..."

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "Error: Please run this script from the HyperFlow root directory"
    exit 1
fi

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed"
    exit 1
fi

# Check for pip
if ! command -v pip3 &> /dev/null; then
    echo "Error: pip3 is required but not installed"
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create config directory
mkdir -p ~/.config/hyperflow

echo ""
echo "Installation completed successfully!"
echo ""
echo "To activate the virtual environment, run:"
echo "  source venv/bin/activate"
echo ""
echo "To start the HyperFlow daemon, run:"
echo "  python main.py daemon"
echo ""
echo "To launch the GUI editor, run:"
echo "  python main.py editor"
echo ""
echo "To auto-start with Hyprland, add this to your hyprland.conf:"
echo "  exec-once = cd /path/to/hyperflow && source venv/bin/activate && python main.py daemon"