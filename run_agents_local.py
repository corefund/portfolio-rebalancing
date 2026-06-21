#!/usr/bin/env python3
"""
Local test runner - simulates 3 Colab agents locally
Generates portfolio proposals without creating PRs
"""

import os
import json
import requests
from pathlib import Path

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

def load_portfolio():
    with open("experiment/initial_portfolio.json") as f:
        return json.load(f)

def load_prompt():
    with open("experiment/agent_prompt.md") as f:
        return f.read()

def call_claude(prompt: str, agent_id: str) -> str:
    """Call Claude API"""
    url = "https://api.anthropic.com/v1/messages"

    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }

    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 4000,
        "temperature": 0.7,
        "messages": [{"role": "user", "content": prompt}]
    }

    print(f"  🤖 Calling Claude API for {agent_id}...")
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()

    result = response.json()
    return result["content"][0]["text"]

def extract_json(response: str) -> dict:
    """Extract JSON from Claude response"""
    start = response.find("{")
    end = response.rfind("}") + 1

    if start == -1 or end == 0:
        raise ValueError("No JSON found")

    json_str = response[start:end]
    return json.loads(json_str)

def save_portfolio(portfolio: dict, agent_id: str, generation: int):
    """Save portfolio to results"""
    os.makedirs("experiment/results", exist_ok=True)

    output_file = f"experiment/results/gen{generation}_{agent_id}_portfolio.json"
    with open(output_file, "w") as f:
        json.dump(portfolio, f, indent=2)

    print(f"  ✅ Saved to {output_file}")

def run_agent(agent_id: str, generation: int):
    """Run one agent"""
    print(f"\n{'='*60}")
    print(f"Agent: {agent_id} | Generation: {generation}")
    print(f"{'='*60}")

    # Load inputs
    portfolio = load_portfolio()
    prompt_template = load_prompt()

    # Build prompt
    prompt = f"""{prompt_template}

## Current Portfolio (Generation {generation})

```json
{json.dumps(portfolio, indent=2)}
```

## Asset Universe

Available from: https://docs.google.com/spreadsheets/d/1f3xJomL2UlCn7887jpX_MQZBsQWbmVKiQXsUdZ3kkcE/export?format=csv

Includes: US stocks (AAPL, MSFT, GOOGL, ...), ETFs (SPY, QQQ, AGG, ...), Crypto (BTC-USD, ETH-USD, ...)

## Your Agent ID

{agent_id}

---

Now propose your rebalanced portfolio as JSON:
"""

    # Call Claude
    response = call_claude(prompt, agent_id)

    # Extract JSON
    print(f"  📝 Parsing response...")
    proposed = extract_json(response)

    # Add agent metadata
    proposed["agent_name"] = agent_id
    proposed["generation"] = generation

    # Validate
    total = sum(a["weight"] for a in proposed["assets"])
    print(f"  📊 Total weight: {total:.4f}")
    print(f"  📊 Num assets: {len(proposed['assets'])}")
    print(f"  📊 Expected Sharpe: {proposed.get('expected_sharpe', 'N/A')}")

    # Save
    save_portfolio(proposed, agent_id, generation)

    return proposed

def main():
    print("🚀 Running 3 agents locally for Generation 0")
    print("=" * 60)

    agents = ["agent_1", "agent_2", "agent_3"]
    generation = 0

    results = []

    for agent_id in agents:
        try:
            portfolio = run_agent(agent_id, generation)
            results.append(portfolio)
        except Exception as e:
            print(f"  ❌ Error: {e}")
            continue

    print(f"\n{'='*60}")
    print(f"✅ Generated {len(results)}/3 portfolios")
    print(f"{'='*60}")

    if results:
        print("\n📊 Summary:")
        for p in results:
            agent = p.get("agent_name", "Unknown")
            sharpe = p.get("expected_sharpe", 0)
            assets = len(p["assets"])
            print(f"  • {agent}: Sharpe={sharpe:.2f}, Assets={assets}")

    return 0

if __name__ == "__main__":
    exit(main())
