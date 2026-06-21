#!/usr/bin/env python3
"""
Generate mock portfolio results for testing
Creates 3 diverse portfolios to demonstrate the system
"""

import json
import random
from pathlib import Path

# Define asset universe by category
TECH_STOCKS = ["AAPL", "MSFT", "GOOGL", "NVDA", "META", "AMZN", "TSLA"]
FINANCE = ["JPM", "BAC", "GS", "V", "MA"]
HEALTHCARE = ["JNJ", "UNH", "PFE", "ABBV"]
ETFS_EQUITY = ["SPY", "QQQ", "IWM", "VTI"]
ETFS_BONDS = ["AGG", "BND", "TLT", "LQD"]
CRYPTO = ["BTC-USD", "ETH-USD", "SOL-USD"]
COMMODITIES = ["GLD", "SLV", "USO"]

def generate_portfolio(agent_id: str, strategy: str) -> dict:
    """Generate a portfolio based on strategy"""

    if strategy == "tech_growth":
        # Tech-heavy growth portfolio
        assets = [
            {"ticker": "NVDA", "weight": 0.20, "reason": "AI/GPU dominance"},
            {"ticker": "MSFT", "weight": 0.15, "reason": "Cloud and AI integration"},
            {"ticker": "GOOGL", "weight": 0.12, "reason": "Search + AI moat"},
            {"ticker": "AAPL", "weight": 0.10, "reason": "Services growth"},
            {"ticker": "BTC-USD", "weight": 0.10, "reason": "Tech adoption proxy"},
            {"ticker": "SPY", "weight": 0.15, "reason": "Market exposure"},
            {"ticker": "AGG", "weight": 0.10, "reason": "Risk balance"},
            {"ticker": "GLD", "weight": 0.08, "reason": "Inflation hedge"}
        ]
        expected_sharpe = 1.65
        explanation = "Tech-concentrated growth strategy with 57% in mega-cap tech. Added crypto for correlation diversification. Bonds and gold for downside protection."

    elif strategy == "balanced":
        # Balanced diversified portfolio
        assets = [
            {"ticker": "SPY", "weight": 0.25, "reason": "Core equity exposure"},
            {"ticker": "AGG", "weight": 0.20, "reason": "Fixed income stability"},
            {"ticker": "MSFT", "weight": 0.12, "reason": "Quality tech"},
            {"ticker": "JNJ", "weight": 0.10, "reason": "Defensive healthcare"},
            {"ticker": "GLD", "weight": 0.10, "reason": "Inflation protection"},
            {"ticker": "BTC-USD", "weight": 0.08, "reason": "Alternative asset"},
            {"ticker": "VTI", "weight": 0.08, "reason": "Broad market"},
            {"ticker": "BND", "weight": 0.07, "reason": "Additional bonds"}
        ]
        expected_sharpe = 1.42
        explanation = "Balanced 60/40-style allocation with moderate tech exposure. Diversified across equities, bonds, commodities, and crypto. Lower volatility target."

    else:  # defensive
        # Conservative defensive portfolio
        assets = [
            {"ticker": "AGG", "weight": 0.22, "reason": "Core bonds"},
            {"ticker": "BND", "weight": 0.18, "reason": "Additional fixed income"},
            {"ticker": "SPY", "weight": 0.15, "reason": "Equity exposure"},
            {"ticker": "JNJ", "weight": 0.12, "reason": "Defensive healthcare"},
            {"ticker": "GLD", "weight": 0.12, "reason": "Safe haven"},
            {"ticker": "V", "weight": 0.08, "reason": "Stable growth"},
            {"ticker": "TLT", "weight": 0.08, "reason": "Long duration bonds"},
            {"ticker": "LQD", "weight": 0.05, "reason": "Corporate bonds"}
        ]
        expected_sharpe = 1.28
        explanation = "Conservative portfolio with 53% bonds for capital preservation. Defensive equity selection (healthcare, payments). Gold as portfolio insurance. Lower expected return but reduced drawdown."

    portfolio = {
        "generation": 0,
        "portfolio_id": f"{agent_id}_gen0",
        "agent_name": agent_id,
        "assets": assets,
        "total_weight": sum(a["weight"] for a in assets),
        "expected_sharpe": expected_sharpe,
        "explanation": explanation
    }

    return portfolio

def main():
    print("📝 Generating mock portfolios for demonstration...")

    strategies = [
        ("agent_1", "tech_growth"),
        ("agent_2", "balanced"),
        ("agent_3", "defensive")
    ]

    os.makedirs("experiment/results", exist_ok=True)

    for agent_id, strategy in strategies:
        portfolio = generate_portfolio(agent_id, strategy)

        output_file = f"experiment/results/gen0_{agent_id}_portfolio.json"
        with open(output_file, "w") as f:
            json.dump(portfolio, f, indent=2)

        print(f"✅ {agent_id} ({strategy}): Sharpe={portfolio['expected_sharpe']:.2f}, Assets={len(portfolio['assets'])}")
        print(f"   Saved to {output_file}")

    print("\n✅ Generated 3 mock portfolios")
    print("\nNext: Run 'python orchestrator.py' to see results")

if __name__ == "__main__":
    import os
    exit(main())
