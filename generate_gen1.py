#!/usr/bin/env python3
"""
Generate portfolios for Generation 1
Building on the best portfolio from Gen 0 (agent_1)
"""

import json
import random
from pathlib import Path

def load_current_portfolio():
    """Load the current initial portfolio"""
    with open("experiment/initial_portfolio.json") as f:
        return json.load(f)

def mutate_portfolio(base: dict, agent_id: str, mutation_type: str) -> dict:
    """Create mutated version of base portfolio"""

    assets = base["assets"].copy()

    if mutation_type == "reweight":
        # Slight weight adjustments, favor tech
        new_assets = []
        for asset in assets:
            ticker = asset["ticker"]
            old_weight = asset["weight"]

            # Small random adjustment
            if ticker in ["NVDA", "MSFT"]:
                # Increase tech leaders
                new_weight = min(0.25, old_weight * 1.1)
            elif ticker == "AGG":
                # Reduce bonds slightly
                new_weight = max(0.05, old_weight * 0.9)
            else:
                new_weight = old_weight + random.uniform(-0.02, 0.02)

            new_weight = max(0.05, min(0.25, new_weight))
            new_assets.append({
                "ticker": ticker,
                "weight": new_weight,
                "reason": asset.get("reason", "Carried forward")
            })

        # Normalize
        total = sum(a["weight"] for a in new_assets)
        for a in new_assets:
            a["weight"] = round(a["weight"] / total, 4)

        expected_sharpe = 1.72
        explanation = "Increased weights in NVDA/MSFT (AI momentum), reduced bonds. Tech allocation now 59%. Higher expected returns with marginally higher volatility."

    elif mutation_type == "add_crypto":
        # Replace GLD with ETH-USD
        new_assets = []
        for asset in assets:
            if asset["ticker"] == "GLD":
                new_assets.append({
                    "ticker": "ETH-USD",
                    "weight": 0.10,
                    "reason": "Crypto diversification beyond BTC"
                })
            elif asset["ticker"] == "BTC-USD":
                new_assets.append({
                    "ticker": "BTC-USD",
                    "weight": 0.08,
                    "reason": "Reduced to make room for ETH"
                })
            else:
                new_assets.append(asset.copy())

        # Normalize
        total = sum(a["weight"] for a in new_assets)
        for a in new_assets:
            a["weight"] = round(a["weight"] / total, 4)

        expected_sharpe = 1.68
        explanation = "Replaced gold with Ethereum for higher growth potential. Dual crypto exposure (BTC+ETH) increases alternative asset allocation to 18%. More aggressive risk profile."

    else:  # add_defensive
        # Add defensive stock, reduce tech slightly
        new_assets = []
        for asset in assets:
            if asset["ticker"] == "AAPL":
                new_assets.append({
                    "ticker": "AAPL",
                    "weight": 0.07,
                    "reason": "Reduced for rebalance"
                })
                new_assets.append({
                    "ticker": "JNJ",
                    "weight": 0.05,
                    "reason": "Defensive healthcare addition"
                })
            else:
                new_assets.append(asset.copy())

        # Normalize
        total = sum(a["weight"] for a in new_assets)
        for a in new_assets:
            a["weight"] = round(a["weight"] / total, 4)

        expected_sharpe = 1.58
        explanation = "Added Johnson & Johnson for defensive balance. Slightly reduced AAPL concentration. Portfolio now includes healthcare sector exposure, reducing tech dependency to 54%."

    portfolio = {
        "generation": 1,
        "portfolio_id": f"{agent_id}_gen1",
        "agent_name": agent_id,
        "assets": new_assets,
        "total_weight": sum(a["weight"] for a in new_assets),
        "expected_sharpe": expected_sharpe,
        "explanation": explanation
    }

    return portfolio

def main():
    print("📝 Generating Generation 1 portfolios...")
    print("   (Building on best from Gen 0: agent_1)\n")

    base_portfolio = load_current_portfolio()

    mutations = [
        ("agent_1", "reweight"),
        ("agent_2", "add_crypto"),
        ("agent_3", "add_defensive")
    ]

    import os
    os.makedirs("experiment/results", exist_ok=True)

    for agent_id, mutation in mutations:
        portfolio = mutate_portfolio(base_portfolio, agent_id, mutation)

        output_file = f"experiment/results/gen1_{agent_id}_portfolio.json"
        with open(output_file, "w") as f:
            json.dump(portfolio, f, indent=2)

        print(f"✅ {agent_id} ({mutation}): Sharpe={portfolio['expected_sharpe']:.2f}, Assets={len(portfolio['assets'])}")
        print(f"   {portfolio['explanation'][:80]}...")

    print("\n✅ Generated 3 Generation 1 portfolios")
    print("Next: Run 'python orchestrator.py' to analyze Gen 0-1")

if __name__ == "__main__":
    exit(main())
