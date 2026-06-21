#!/bin/bash
# init.sh - Setup script for Colab agent deployment

set -e

AGENT_ID=${1:-"agent_1"}
GENERATION=${2:-"0"}

echo "🚀 Setting up Colab agent: $AGENT_ID (Generation $GENERATION)"

# Install dependencies
echo "📦 Installing dependencies..."
pip install -q anthropic requests pyyaml

# Clone repository
echo "📁 Cloning repository..."
if [ -d "portfolio-rebalancing" ]; then
    cd portfolio-rebalancing
    git pull origin master
else
    git clone https://github.com/wtf403/portfolio-rebalancing.git
    cd portfolio-rebalancing
fi

# Set environment
export AGENT_ID="$AGENT_ID"
export GENERATION="$GENERATION"

echo "✅ Setup complete"
echo "   Agent ID: $AGENT_ID"
echo "   Generation: $GENERATION"
echo "   Ready to run: python colab_agent.py"
