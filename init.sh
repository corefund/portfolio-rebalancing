#!/bin/bash
# init.sh - Initialize Colab machine for GA experiment
# Installs Claude CLI, xpra, dependencies, and clones repository

set -e

echo "🚀 Initializing Colab machine for GA portfolio experiment"
echo ""

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -q anthropic requests pandas pyyaml 2>/dev/null || true

# Install Claude Code CLI (if not present)
if ! command -v claude &> /dev/null; then
    echo "📥 Installing Claude Code CLI..."
    curl -fsSL https://raw.githubusercontent.com/anthropics/claude-code/main/install.sh | bash
fi

# Install xpra for GUI forwarding (optional, non-blocking)
echo "📺 Installing xpra..."
apt-get update -qq 2>/dev/null || true
apt-get install -y -qq xpra 2>/dev/null || true

# Configure git
echo "⚙️  Configuring git..."
git config --global user.name "GA-Agent"
git config --global user.email "agent@experiment.local"

# Clone repository
echo "📁 Cloning repository..."
cd /content
if [ -d "portfolio-rebalancing" ]; then
    cd portfolio-rebalancing
    git pull origin master 2>/dev/null || true
    echo "✅ Repository updated"
else
    git clone https://github.com/wtf403/portfolio-rebalancing.git
    echo "✅ Repository cloned"
fi

# Copy settings.json if provided
if [ -f "/content/settings.json" ]; then
    cp /content/settings.json /content/portfolio-rebalancing/settings.json
    echo "✅ settings.json copied"
fi

echo ""
echo "✅ Machine initialization complete!"
echo "   Claude CLI: $(which claude 2>/dev/null || echo 'not installed')"
echo "   Python deps: ✓"
echo "   Repository: /content/portfolio-rebalancing"
echo ""
echo "Ready to run agents!"
