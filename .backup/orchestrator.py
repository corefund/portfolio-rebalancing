#!/usr/bin/env python3
"""
Orchestrator for GA experiment
Manages generations, selects best portfolios, updates initial state
"""

import json
import shutil
from pathlib import Path
from typing import List, Dict
import pandas as pd


def load_generation_results(generation: int) -> List[Dict]:
    """Load all portfolio proposals from a generation"""
    results_dir = Path("experiment/results")
    pattern = f"gen{generation}_*_portfolio.json"

    portfolios = []
    for file_path in results_dir.glob(pattern):
        with open(file_path) as f:
            portfolio = json.load(f)
            portfolio['file'] = file_path.name
            portfolios.append(portfolio)

    return portfolios


def calculate_simple_fitness(portfolio: Dict) -> float:
    """
    Calculate simple fitness score
    In real experiment, would backtest on historical data
    For now, use expected_sharpe from agent if available
    """
    # Use agent's estimate
    if 'expected_sharpe' in portfolio:
        return float(portfolio['expected_sharpe'])

    # Fallback: penalize concentration
    weights = [asset['weight'] for asset in portfolio['assets']]
    max_weight = max(weights)
    diversity_bonus = 1.0 - max_weight  # Higher bonus for more diverse

    return diversity_bonus


def select_best_portfolios(portfolios: List[Dict], k: int = 1) -> List[Dict]:
    """
    Select top k portfolios by fitness
    This is the selection phase of GA
    """
    # Calculate fitness for each
    for portfolio in portfolios:
        portfolio['fitness'] = calculate_simple_fitness(portfolio)

    # Sort by fitness descending
    portfolios.sort(key=lambda p: p['fitness'], reverse=True)

    return portfolios[:k]


def print_generation_summary(generation: int, portfolios: List[Dict]):
    """Print summary of generation results"""
    print(f"\n{'='*60}")
    print(f"Generation {generation} Summary")
    print(f"{'='*60}")
    print(f"Total portfolios: {len(portfolios)}")

    if not portfolios:
        print("No portfolios found!")
        return

    print(f"\n{'Agent':<15} {'Fitness':<10} {'Assets':<8} {'Max Weight':<12}")
    print("-" * 60)

    for p in portfolios:
        agent_name = p.get('agent_name', 'Unknown')
        fitness = p.get('fitness', 0.0)
        num_assets = len(p['assets'])
        max_weight = max(asset['weight'] for asset in p['assets'])

        print(f"{agent_name:<15} {fitness:<10.4f} {num_assets:<8} {max_weight:<12.2%}")

    # Best portfolio
    best = portfolios[0]
    print(f"\n🏆 Best Portfolio: {best.get('agent_name', 'Unknown')}")
    print(f"   Fitness: {best['fitness']:.4f}")
    print(f"   Assets:")

    for asset in best['assets'][:5]:  # Show top 5
        print(f"   - {asset['ticker']}: {asset['weight']:.2%}")

    if len(best['assets']) > 5:
        print(f"   ... and {len(best['assets']) - 5} more")


def update_initial_portfolio(best_portfolio: Dict):
    """Update initial_portfolio.json for next generation"""
    initial_path = Path("experiment/initial_portfolio.json")

    # Backup current
    backup_path = initial_path.with_suffix('.json.bak')
    shutil.copy(initial_path, backup_path)

    # Create new initial portfolio from best
    new_initial = {
        "generation": best_portfolio['generation'] + 1,
        "portfolio_id": f"gen{best_portfolio['generation'] + 1}_initial",
        "assets": best_portfolio['assets'],
        "total_weight": sum(asset['weight'] for asset in best_portfolio['assets']),
        "parent": best_portfolio['portfolio_id'],
        "parent_fitness": best_portfolio['fitness']
    }

    with open(initial_path, 'w') as f:
        json.dump(new_initial, f, indent=2)

    print(f"\n✅ Updated initial_portfolio.json for generation {new_initial['generation']}")


def export_metrics(all_generations: List[List[Dict]], output_path: str = "experiment/metrics.csv"):
    """Export all metrics to CSV for analysis"""
    rows = []

    for gen_num, portfolios in enumerate(all_generations):
        for portfolio in portfolios:
            row = {
                'generation': gen_num,
                'agent': portfolio.get('agent_name', 'Unknown'),
                'fitness': portfolio.get('fitness', 0.0),
                'num_assets': len(portfolio['assets']),
                'max_weight': max(asset['weight'] for asset in portfolio['assets']),
                'min_weight': min(asset['weight'] for asset in portfolio['assets']),
                'expected_sharpe': portfolio.get('expected_sharpe', None)
            }
            rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    print(f"\n📊 Exported metrics to {output_path}")


def main():
    """Run orchestration for completed generations"""
    print("🎯 Portfolio GA Orchestrator")
    print("=" * 60)

    results_dir = Path("experiment/results")
    if not results_dir.exists():
        print("❌ No results directory found. Run agents first!")
        return 1

    # Detect available generations
    all_files = list(results_dir.glob("gen*_*_portfolio.json"))

    if not all_files:
        print("❌ No portfolio files found. Run agents first!")
        return 1

    # Extract generation numbers
    generations = set()
    for file_path in all_files:
        parts = file_path.stem.split('_')
        gen_str = parts[0]  # gen0, gen1, etc.
        gen_num = int(gen_str.replace('gen', ''))
        generations.add(gen_num)

    generations = sorted(generations)
    print(f"📁 Found generations: {generations}")

    # Process each generation
    all_generation_data = []

    for gen in generations:
        portfolios = load_generation_results(gen)

        if not portfolios:
            print(f"\n⚠️  Generation {gen}: No portfolios found")
            continue

        # Select best
        best_portfolios = select_best_portfolios(portfolios, k=1)

        # Store
        all_generation_data.append(portfolios)

        # Print summary
        print_generation_summary(gen, portfolios)

    # Export metrics
    if all_generation_data:
        export_metrics(all_generation_data)

    # Ask to update initial portfolio for next generation
    if all_generation_data:
        latest_gen = generations[-1]
        latest_portfolios = all_generation_data[-1]
        best = select_best_portfolios(latest_portfolios, k=1)[0]

        print(f"\n{'='*60}")
        print("Next Generation Setup")
        print(f"{'='*60}")
        print(f"Current generation: {latest_gen}")
        print(f"Best portfolio: {best.get('agent_name', 'Unknown')} (fitness: {best['fitness']:.4f})")

        response = input("\n🔄 Update initial_portfolio.json for next generation? (y/n): ")

        if response.lower() == 'y':
            update_initial_portfolio(best)
            print(f"\n✅ Ready for generation {latest_gen + 1}")
            print(f"   Set GENERATION={latest_gen + 1} in Colab notebooks and re-run agents")
        else:
            print("\n⏭️  Skipped update")

    print("\n✨ Orchestration complete!")
    return 0


if __name__ == "__main__":
    exit(main())
