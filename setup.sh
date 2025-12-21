#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Claude Code to Kiro CLI Agent Converter - Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if Kiro CLI is installed
if ! command -v kiro-cli &> /dev/null; then
    echo -e "${RED}✗ Kiro CLI is not installed${NC}"
    echo ""
    echo "Install Kiro CLI first:"
    echo "  curl -fsSL https://cli.kiro.dev/install | bash"
    echo ""
    exit 1
fi

echo -e "${GREEN}✓ Kiro CLI is installed${NC}"
KIRO_VERSION=$(kiro-cli version 2>/dev/null | head -n 1 || echo "unknown")
echo "  Version: $KIRO_VERSION"
echo ""

# Check Python and uv
if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}uv is not installed${NC}"
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.cargo/env
fi

echo -e "${GREEN}✓ uv is installed${NC}"
UV_VERSION=$(uv --version)
echo "  $UV_VERSION"
echo ""

# Clone wshobson/agents if not exists
AGENTS_DIR="./wshobson-agents"

if [ -d "$AGENTS_DIR" ]; then
    echo "📁 wshobson/agents already exists at $AGENTS_DIR"
    read -p "   Update it? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "   Updating..."
        cd "$AGENTS_DIR" && git pull && cd ..
        echo -e "${GREEN}✓ Updated${NC}"
    fi
else
    echo "📥 Cloning wshobson/agents..."
    git clone -q https://github.com/wshobson/agents.git "$AGENTS_DIR"
    echo -e "${GREEN}✓ Cloned to $AGENTS_DIR${NC}"
fi
echo ""

# Ask for output directory
DEFAULT_OUTPUT="$HOME/.kiro/agents"
echo "📂 Output directory for converted agents"
echo "   Default: $DEFAULT_OUTPUT"
read -p "   Use default? (Y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Nn]$ ]]; then
    read -p "   Enter output directory: " OUTPUT_DIR
else
    OUTPUT_DIR="$DEFAULT_OUTPUT"
fi

# Check if output directory exists and has files
if [ -d "$OUTPUT_DIR" ] && [ "$(ls -A $OUTPUT_DIR/*.json 2>/dev/null)" ]; then
    echo ""
    echo -e "${YELLOW}⚠ Warning: Output directory already contains agent files${NC}"
    echo "   Location: $OUTPUT_DIR"
    ls "$OUTPUT_DIR"/*.json 2>/dev/null | head -5
    echo ""
    read -p "   Backup existing agents? (Y/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        BACKUP_DIR="${OUTPUT_DIR}.backup.$(date +%Y%m%d-%H%M%S)"
        echo "   Creating backup at $BACKUP_DIR"
        cp -r "$OUTPUT_DIR" "$BACKUP_DIR"
        echo -e "${GREEN}✓ Backup created${NC}"
    fi
fi

echo ""
echo "🔄 Starting conversion..."
echo "   Source: $AGENTS_DIR"
echo "   Output: $OUTPUT_DIR"
echo ""

# Run dry-run first
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Dry Run (Preview)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
uv run --with pyyaml python claude_to_kiro_converter.py \
    --source "$AGENTS_DIR" \
    --output "$OUTPUT_DIR" \
    --dry-run

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
read -p "Proceed with conversion? (Y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Nn]$ ]]; then
    echo "Conversion cancelled."
    exit 0
fi

# Actual conversion
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Converting Agents"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
uv run --with pyyaml python claude_to_kiro_converter.py \
    --source "$AGENTS_DIR" \
    --output "$OUTPUT_DIR" \
    --create-index

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✓ Conversion complete!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Show statistics
if [ -f "$OUTPUT_DIR/agents_index.md" ]; then
    echo "📊 Statistics:"
    # Parse markdown file for stats roughly
    COUNT=$(grep -c "\- \*\*" "$OUTPUT_DIR/agents_index.md")
    echo "   Total agents: ~$COUNT"
    echo ""
    echo "   Index file created at: $OUTPUT_DIR/agents_index.md"
    echo ""
fi

# Test agent listing
echo "🧪 Testing agent listing..."
kiro-cli agent list 2>/dev/null | head -10 || echo "   Run 'kiro-cli agent list' to see all agents"
echo ""

# Offer to test an agent
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Next Steps"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. View all agents:"
echo "   kiro-cli agent list"
echo ""
echo "2. View agent index:"
echo "   cat $OUTPUT_DIR/agents_index.md"
echo ""
echo "3. Test an agent:"
echo "   kiro-cli chat --agent python-pro"
echo ""
echo "4. Customize an agent:"
echo "   kiro-cli agent edit python-pro"
echo ""
echo "5. Set a default agent:"
echo "   kiro-cli agent set-default python-pro"
echo ""

read -p "Test an agent now? (y/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Get random agent from INDEX
    if [ -f "$OUTPUT_DIR/INDEX.json" ]; then
        RANDOM_AGENT=$(jq -r '.agents[0].name' "$OUTPUT_DIR/INDEX.json")
        echo ""
        echo "Testing agent: $RANDOM_AGENT"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        kiro-cli chat --agent "$RANDOM_AGENT" "Hello, please introduce yourself in 2-3 sentences."
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}All done! Happy coding with Kiro! 🚀${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
