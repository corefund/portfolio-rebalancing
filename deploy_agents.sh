#!/bin/bash
# deploy_agents.sh - Deploy 3 agents to existing Colab sessions

set -e

# Check for required environment variables
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "❌ ANTHROPIC_API_KEY not set"
    exit 1
fi

if [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ GITHUB_TOKEN not set"
    exit 1
fi

echo "🚀 Deploying 3 agents to Colab sessions..."

# Get active sessions
SESSIONS=$(colab sessions | grep "SSH:" | awk '{print $2, $3, $4}')

# Parse sessions
SESSION_1=$(echo "$SESSIONS" | sed -n '1p' | awk '{print $2"@"$3}' | sed 's/root@//;s/-p//')
SESSION_2=$(echo "$SESSIONS" | sed -n '2p' | awk '{print $2"@"$3}' | sed 's/root@//;s/-p//')
SESSION_3=$(echo "$SESSIONS" | sed -n '3p' | awk '{print $2"@"$3}' | sed 's/root@//;s/-p//')

echo "📡 Sessions found:"
echo "   1: $SESSION_1"
echo "   2: $SESSION_2"
echo "   3: $SESSION_3"

# Deploy to each session
deploy_agent() {
    local HOST=$1
    local PORT=$2
    local AGENT_ID=$3
    local GENERATION=${4:-0}

    echo ""
    echo "🔧 Deploying $AGENT_ID to $HOST:$PORT..."

    # Upload init script
    scp -P "$PORT" -o StrictHostKeyChecking=no init.sh "root@$HOST:/tmp/"

    # Upload agent script
    scp -P "$PORT" -o StrictHostKeyChecking=no colab_agent.py "root@$HOST:/tmp/"

    # Set environment and run
    ssh -p "$PORT" -o StrictHostKeyChecking=no "root@$HOST" << EOF
export ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY"
export GITHUB_TOKEN="$GITHUB_TOKEN"
export AGENT_ID="$AGENT_ID"
export GENERATION="$GENERATION"
cd /tmp
bash init.sh "$AGENT_ID" "$GENERATION"
EOF

    echo "✅ $AGENT_ID deployed"
}

# Extract host and port from session strings
parse_session() {
    local SESSION=$1
    local HOST=$(echo "$SESSION" | cut -d':' -f1)
    local PORT=$(echo "$SESSION" | cut -d':' -f2)
    echo "$HOST $PORT"
}

# Deploy agent_1
read HOST1 PORT1 <<< $(parse_session "$SESSION_1")
deploy_agent "$HOST1" "$PORT1" "agent_1" 0

# Deploy agent_2
read HOST2 PORT2 <<< $(parse_session "$SESSION_2")
deploy_agent "$HOST2" "$PORT2" "agent_2" 0

# Deploy agent_3
read HOST3 PORT3 <<< $(parse_session "$SESSION_3")
deploy_agent "$HOST3" "$PORT3" "agent_3" 0

echo ""
echo "✅ All 3 agents deployed!"
echo ""
echo "To run agents:"
echo "  ssh root@$HOST1 -p $PORT1 'cd portfolio-rebalancing && python colab_agent.py'"
echo "  ssh root@$HOST2 -p $PORT2 'cd portfolio-rebalancing && python colab_agent.py'"
echo "  ssh root@$HOST3 -p $PORT3 'cd portfolio-rebalancing && python colab_agent.py'"
