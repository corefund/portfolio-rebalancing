#!/bin/bash
# Deploy and run agents on 3 Colab machines using colab exec

set -e

# Load environment
source .env

SESSION_1="agent_2"
SESSION_2="agent_3" 
SESSION_3="6a5000"

AGENT_IDS=("agent_1" "agent_2" "agent_3")
SESSIONS=("$SESSION_3" "$SESSION_1" "$SESSION_2")

echo "🚀 Deploying 3 agents to Colab sessions..."
echo ""

# Function to deploy single agent
deploy_agent() {
    local SESSION=$1
    local AGENT_ID=$2
    local GENERATION=${3:-0}
    
    echo "📡 Deploying $AGENT_ID to session $SESSION..."
    
    # Create Python script for this agent
    cat > /tmp/agent_${AGENT_ID}.py << 'PYEOF'
import os, subprocess, sys

AGENT_ID = os.environ.get("AGENT_ID", "agent_1")
GENERATION = os.environ.get("GENERATION", "0")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

print(f"🚀 Setting up {AGENT_ID} (Gen {GENERATION})")

# Install deps
print("📦 Installing dependencies...")
subprocess.run(["pip", "install", "-q", "anthropic", "requests", "pyyaml"], check=False)

# Clone repo
print("📥 Cloning repository...")
if os.path.exists("portfolio-rebalancing"):
    os.chdir("portfolio-rebalancing")
    subprocess.run(["git", "pull", "origin", "master"], check=False)
else:
    subprocess.run(["git", "clone", "https://github.com/wtf403/portfolio-rebalancing.git"], check=True)
    os.chdir("portfolio-rebalancing")

# Set env
os.environ["AGENT_ID"] = AGENT_ID
os.environ["GENERATION"] = GENERATION
os.environ["ANTHROPIC_API_KEY"] = ANTHROPIC_API_KEY
os.environ["GITHUB_TOKEN"] = GITHUB_TOKEN

print(f"✅ Setup complete. Running {AGENT_ID}...")

# Run agent
subprocess.run([sys.executable, "colab_agent.py"], check=True)
print(f"✅ {AGENT_ID} completed!")
PYEOF
    
    # Execute on Colab
    AGENT_ID=$AGENT_ID GENERATION=$GENERATION \
    ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY GITHUB_TOKEN=$GITHUB_TOKEN \
    colab exec -s "$SESSION" -f /tmp/agent_${AGENT_ID}.py --timeout 600
    
    echo "✅ $AGENT_ID deployment complete"
    echo ""
}

# Deploy all 3 agents in parallel
for i in 0 1 2; do
    deploy_agent "${SESSIONS[$i]}" "${AGENT_IDS[$i]}" 0 &
done

echo "⏳ Waiting for all agents to complete..."
wait

echo ""
echo "🎉 All 3 agents deployed and executed!"
echo ""
echo "Check PRs at: https://github.com/wtf403/portfolio-rebalancing/pulls"
