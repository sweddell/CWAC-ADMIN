#!/bin/bash
#
# Prepare CWAC-ADMIN for Initial GitHub Commit
# Cleans up results, database, and temporary files
#

set -e

echo "=========================================="
echo "Preparing CWAC-ADMIN for GitHub Commit"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo -e "${BLUE}📋 Cleaning up results directory...${NC}"
# Remove all scan results but keep .gitkeep
if [ -d "$SCRIPT_DIR/results" ]; then
    find "$SCRIPT_DIR/results" -mindepth 1 -not -name '.gitkeep' -delete
    echo -e "${GREEN}✅ Results directory cleaned${NC}"
else
    echo -e "${YELLOW}⚠️  Results directory not found${NC}"
fi

echo ""
echo -e "${BLUE}🗄️  Cleaning up database...${NC}"
# Remove database files (will be recreated from schema on first run)
if [ -f "$SCRIPT_DIR/cwac_admin_app/database/bi_integration/cwac_analytics.db" ]; then
    rm "$SCRIPT_DIR/cwac_admin_app/database/bi_integration/cwac_analytics.db"
    echo -e "${GREEN}✅ Database file removed (will be recreated from schema)${NC}"
else
    echo -e "${YELLOW}⚠️  Database file not found${NC}"
fi

echo ""
echo -e "${BLUE}📝 Cleaning up log files...${NC}"
# Remove log files
if [ -d "$SCRIPT_DIR/logs" ]; then
    rm -rf "$SCRIPT_DIR/logs"/*
    echo -e "${GREEN}✅ Log files cleaned${NC}"
else
    mkdir -p "$SCRIPT_DIR/logs"
    echo -e "${GREEN}✅ Logs directory created${NC}"
fi

echo ""
echo -e "${BLUE}👤 Cleaning up user data...${NC}"
# Remove users.json (default admin account will be created on first run)
if [ -f "$SCRIPT_DIR/admin/users.json" ]; then
    rm "$SCRIPT_DIR/admin/users.json"
    echo -e "${GREEN}✅ User data removed (default admin will be created)${NC}"
else
    echo -e "${YELLOW}⚠️  users.json not found${NC}"
fi

# Remove backup files
if [ -f "$SCRIPT_DIR/admin/accessibility_rules.json.backup" ]; then
    rm "$SCRIPT_DIR/admin/accessibility_rules.json.backup"
    echo -e "${GREEN}✅ Backup files removed${NC}"
fi

echo ""
echo -e "${BLUE}🧹 Cleaning up Python cache...${NC}"
# Remove Python cache files
find "$SCRIPT_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$SCRIPT_DIR" -type f -name "*.pyc" -delete 2>/dev/null || true
find "$SCRIPT_DIR" -type f -name "*.pyo" -delete 2>/dev/null || true
find "$SCRIPT_DIR" -type f -name "*.log" -delete 2>/dev/null || true
echo -e "${GREEN}✅ Python cache cleaned${NC}"

echo ""
echo -e "${BLUE}🧪 Cleaning up test coverage...${NC}"
# Remove test coverage files
if [ -d "$SCRIPT_DIR/htmlcov" ]; then
    rm -rf "$SCRIPT_DIR/htmlcov"
    echo -e "${GREEN}✅ Coverage reports removed${NC}"
fi
if [ -f "$SCRIPT_DIR/.coverage" ]; then
    rm "$SCRIPT_DIR/.coverage"
    echo -e "${GREEN}✅ Coverage data removed${NC}"
fi

echo ""
echo -e "${BLUE}🔍 Verifying CWAC scanner exclusion...${NC}"
# Check if cwac directory exists (should not be committed)
if [ -d "$SCRIPT_DIR/cwac/src" ]; then
    echo -e "${YELLOW}⚠️  CWAC scanner source detected${NC}"
    echo -e "${YELLOW}   This directory should NOT be committed to GitHub${NC}"
    echo -e "${YELLOW}   It's installed via install_cwac.sh${NC}"
else
    echo -e "${GREEN}✅ CWAC scanner not present (will be installed via script)${NC}"
fi

echo ""
echo "=========================================="
echo "Cleanup Complete!"
echo "=========================================="
echo ""
echo -e "${GREEN}✅ Repository is ready for initial commit${NC}"
echo ""
echo "📋 What was cleaned:"
echo "   • Scan results (results/*)"
echo "   • Database file (will be recreated from schema)"
echo "   • Log files"
echo "   • User data (default admin will be created)"
echo "   • Python cache and temporary files"
echo "   • Test coverage reports"
echo ""
echo "📋 What's preserved:"
echo "   • Database schema (schema.sql)"
echo "   • Configuration files"
echo "   • WCAG rules (wcag22_aa_rules.json)"
echo "   • Installation scripts"
echo "   • Documentation"
echo "   • Test suite"
echo ""
echo "🚀 Next steps:"
echo "   1. Review .gitignore to ensure all exclusions are correct"
echo "   2. git add -A"
echo "   3. git commit -m 'Initial commit: CWAC-ADMIN platform'"
echo "   4. git remote add origin <your-repo-url>"
echo "   5. git push -u origin main"
echo ""
echo -e "${BLUE}📚 After cloning, users should:${NC}"
echo "   1. Run ./install_cwac.sh to install CWAC scanner"
echo "   2. Install dependencies: pip install -r requirements.txt"
echo "   3. Start the application: cd cwac_admin_app/app && python3 admin_app.py"
echo ""
