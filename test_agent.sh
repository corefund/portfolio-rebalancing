#!/bin/bash
# Test colab_agent.py locally

echo "Testing portfolio generation agent locally..."
echo "============================================"

# Set environment
export AGENT_ID="test_agent"
export GENERATION="0"
export ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-sk-3e442e3188a33a3c-425a71-32bbb64c}"
export ANTHROPIC_BASE_URL="${ANTHROPIC_BASE_URL:-https://router.plus/v1}"
export ANTHROPIC_MODEL="${ANTHROPIC_MODEL:-gpt-5.5}"

# Run agent
python3 colab_agent.py

# Check result
if [ -f "/tmp/portfolio_gen0_test_agent.json" ]; then
    echo ""
    echo "✅ Portfolio generated successfully!"
    echo ""
    echo "Result:"
    cat /tmp/portfolio_gen0_test_agent.json | python3 -m json.tool

    # Validate
    echo ""
    echo "Running validation..."
    cp /tmp/portfolio_gen0_test_agent.json experiment/results/
    python3 experiment/validate_portfolio.py | grep -A 20 "test_agent"
else
    echo "❌ No portfolio file generated"
    exit 1
fi
