#!/usr/bin/env python3
"""
Validate portfolio proposal from agent
Run by GitHub Actions
"""

import json
import sys
from pathlib import Path
from typing import Dict, List


def find_portfolio_files() -> List[Path]:
    """Find all portfolio JSON files in experiment/results/"""
    results_dir = Path("experiment/results")
    if not results_dir.exists():
        return []

    return list(results_dir.glob("*_portfolio.json"))


def validate_portfolio(portfolio: dict) -> tuple[bool, list[str], dict]:
    """
    Validate portfolio constraints

    Returns:
        (is_valid, errors, metrics)
    """
    errors = []

    # Check required fields
    required_fields = ["generation", "portfolio_id", "assets", "agent_name"]
    for field in required_fields:
        if field not in portfolio:
            errors.append(f"Missing required field: {field}")

    if "assets" not in portfolio:
        return False, errors, {}

    # Calculate metrics
    total_weight = sum(asset.get("weight", 0) for asset in portfolio["assets"])
    num_assets = len(portfolio["assets"])
    weights = [asset.get("weight", 0) for asset in portfolio["assets"]]
    max_weight = max(weights) if weights else 0
    min_weight = min(weights) if weights else 0

    metrics = {
        "total_weight": total_weight,
        "num_assets": num_assets,
        "max_weight": max_weight,
        "min_weight": min_weight
    }

    # Validate total weight
    if abs(total_weight - 1.0) > 0.01:
        errors.append(f"Total weight {total_weight:.4f} must equal 1.0 (±0.01)")

    # Validate number of assets
    if num_assets < 8:
        errors.append(f"Number of assets {num_assets} is below minimum (8)")
    elif num_assets > 12:
        errors.append(f"Number of assets {num_assets} exceeds maximum (12)")

    # Validate individual weights
    for i, asset in enumerate(portfolio["assets"]):
        if "ticker" not in asset:
            errors.append(f"Asset {i} missing ticker")
            continue

        ticker = asset["ticker"]
        weight = asset.get("weight", 0)

        if weight < 0.05:
            errors.append(f"{ticker} weight {weight:.4f} below minimum (0.05)")
        elif weight > 0.25:
            errors.append(f"{ticker} weight {weight:.4f} exceeds maximum (0.25)")

    # Check for duplicate tickers
    tickers = [asset.get("ticker") for asset in portfolio["assets"] if "ticker" in asset]
    if len(tickers) != len(set(tickers)):
        errors.append("Duplicate tickers found in portfolio")

    is_valid = len(errors) == 0

    return is_valid, errors, metrics


def main():
    print("🔍 Validating portfolio proposals...")

    # Find portfolio files
    portfolio_files = find_portfolio_files()

    if not portfolio_files:
        print("❌ No portfolio files found in experiment/results/")
        return 1

    print(f"📂 Found {len(portfolio_files)} portfolio file(s)")

    all_valid = True

    for portfolio_file in portfolio_files:
        print(f"\n📄 Validating {portfolio_file.name}...")

        try:
            with open(portfolio_file) as f:
                portfolio = json.load(f)
        except Exception as e:
            print(f"❌ Failed to load JSON: {e}")
            all_valid = False
            continue

        is_valid, errors, metrics = validate_portfolio(portfolio)

        if is_valid:
            print("✅ Portfolio is valid")
            print(f"   Total weight: {metrics['total_weight']:.4f}")
            print(f"   Assets: {metrics['num_assets']}")
            print(f"   Concentration: {metrics['max_weight']:.2%}")
        else:
            print("❌ Portfolio validation failed:")
            for error in errors:
                print(f"   - {error}")
            all_valid = False

        # Write result for GitHub Actions
        result = {
            "valid": is_valid,
            "errors": errors,
            "metrics": metrics,
            "file": str(portfolio_file)
        }

        with open("validation_result.json", "w") as f:
            json.dump(result, f, indent=2)

    if all_valid:
        print("\n✅ All portfolios are valid")
        return 0
    else:
        print("\n❌ Some portfolios failed validation")
        return 1


if __name__ == "__main__":
    sys.exit(main())
