#!/bin/bash
#
# CWAC Scanner Installation Script
# Installs the Centralised Web Accessibility Checker (GPL v3)
# as a separate dependency for CWAC-ADMIN
#

set -e

echo "=========================================="
echo "CWAC Scanner Installation"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CWAC_DIR="$SCRIPT_DIR/cwac"

# Check Python version
echo "🐍 Checking Python version..."
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
    echo -e "${RED}❌ Error: Python 3.10+ required, found $PYTHON_VERSION${NC}"
    echo ""
    echo "CWAC requires Python 3.10 or higher (3.12+ recommended)."
    echo ""
    echo "Options:"
    echo "  1. Install Python 3.12+:"
    echo "     - macOS: brew install python@3.12"
    echo "     - Ubuntu: sudo apt install python3.12 python3.12-venv"
    echo ""
    echo "  2. Use specific Python version for venv:"
    echo "     python3.12 -m venv .venv"
    echo ""
    exit 1
fi

echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"
echo ""

echo "📦 Installing CWAC Scanner..."
echo ""

# Check if cwac directory exists and is not empty
if [ -d "$CWAC_DIR" ] && [ "$(ls -A $CWAC_DIR 2>/dev/null | grep -v '.gitkeep')" ]; then
    echo -e "${YELLOW}⚠️  CWAC directory already exists and contains files.${NC}"
    read -p "Do you want to reinstall? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Installation cancelled."
        exit 0
    fi
    echo "🗑️  Removing existing CWAC installation..."
    rm -rf "$CWAC_DIR"
fi

# Create cwac directory
mkdir -p "$CWAC_DIR"

echo "📥 Cloning CWAC Scanner repository..."
echo "Repository: https://github.com/GOVTNZ/cwac"
echo ""

# Clone CWAC from official government repository
if git clone https://github.com/GOVTNZ/cwac.git "$CWAC_DIR"; then
    echo -e "${GREEN}✅ CWAC cloned successfully${NC}"
else
    echo -e "${RED}❌ Failed to clone CWAC repository${NC}"
    exit 1
fi

echo ""
echo "📄 Verifying GPL v3 license..."

# Check for LICENSE file
if [ -f "$CWAC_DIR/LICENSE" ]; then
    echo -e "${GREEN}✅ GPL v3 license found${NC}"
else
    echo -e "${YELLOW}⚠️  License file not found in repository${NC}"
fi

echo ""
echo "=========================================="
echo "CWAC Installation Complete!"
echo "=========================================="
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Install CWAC Python dependencies:"
echo "   cd cwac"
echo "   pip install -r requirements.txt"
echo "   cd .."
echo ""
echo "2. Install Chrome for Testing (via npm):"
echo "   cd cwac"
echo "   npm install"
echo "   cd .."
echo ""
echo "3. Copy configuration files:"
echo "   cp config/*.json cwac/config/"
echo ""
echo "4. Initialize the database:"
echo "   sqlite3 cwac_admin_app/database/bi_integration/cwac_analytics.db < cwac_admin_app/database/bi_integration/schema.sql"
echo ""
echo "📚 Documentation:"
echo "   cwac/README.md - CWAC scanner documentation"
echo "   README.md - CWAC-ADMIN platform documentation"
echo "   INSTALLATION.md - Complete installation guide"
echo ""
echo -e "${GREEN}✨ Ready to scan for accessibility issues!${NC}"
