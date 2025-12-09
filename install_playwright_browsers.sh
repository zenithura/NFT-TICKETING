#!/bin/bash
# Script to install Playwright browsers

echo "Installing Playwright browsers..."
echo "This may take a few minutes..."

# Activate virtual environment if it exists
if [ -d "backend/venv" ]; then
    source backend/venv/bin/activate
    echo "Activated virtual environment"
fi

# Install Chromium browser
echo "Installing Chromium..."
python3 -m playwright install chromium

if [ $? -eq 0 ]; then
    echo "✓ Chromium installed successfully!"
else
    echo "✗ Installation failed. Trying alternative method..."
    
    # Try with pip install playwright first
    pip install playwright
    
    # Then install browsers
    python3 -m playwright install chromium
fi

echo ""
echo "Installation complete!"
echo "You can now run: python admin_panel_test.py"

