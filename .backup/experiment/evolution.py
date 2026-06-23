#!/usr/bin/env python3
"""
Genetic Algorithm evolution operators for portfolio optimization
"""

import random
import json
from typing import Dict, List, Tuple
from pathlib import Path


def calculate_fitness(portfolio: Dict) -> float:
    """
    Calculate fitness score for a portfolio

    Components:
    1. Primary: expected_sharpe (if provided by agent)
    2. Diversity bonus: 1 - max_weight (prefer distributed portfolios)
    3. Universe coverage bonus: log(num_assets) (prefer more assets)

    Returns:
        Float fitness score (higher is better)
    """
    # Primary: use agent's Sharpe estimate if available
    base_fitness = portfolio.get('expected_sharpe', 1.0)

    # Diversity bonus
    weights = [asset['weight'] for asset in portfolio['assets']]
    max_weight = max(weights) if weights else 0
    diversity_bonus = (1.0 - max_weight) * 0.5  # Up to +0.5

    # Asset count bonus (encourage exploration)
    import math
    num_assets = len(portfolio['assets'])
    asset_bonus = math.log(num_assets + 1) * 0.1  # Up to ~0.3 for 20 assets

    total_fitness = base_fitness + diversity_bonus + asset_bonus

    return round(total_fitness, 4)


def crossover(parent1: Dict, parent2: Dict) -> Dict:
    """
    Create offspring by blending two parent portfolios

    Strategy:
    1. Include all assets from both parents
    2. Average weights for common assets
    3. Reduce weights for unique assets by 50%
    4. Normalize to sum=1.0

    Args:
        parent1: First parent portfolio
        parent2: Second parent portfolio

    Returns:
        New offspring portfolio
    """
    # Build asset maps
    assets1 = {a['ticker']: a for a in parent1['assets']}
    assets2 = {a['ticker']: a for a in parent2['assets']}

    all_tickers = set(assets1.keys()) | set(assets2.keys())

    offspring_assets = []

    for ticker in all_tickers:
        if ticker in assets1 and ticker in assets2:
            # Common asset: average weights
            weight = (assets1[ticker]['weight'] + assets2[ticker]['weight']) / 2
            reason = f"Blend: {assets1[ticker]['reason'][:30]}"
        elif ticker in assets1:
            # From parent1 only: reduce weight
            weight = assets1[ticker]['weight'] * 0.5
            reason = assets1[ticker]['reason']
        else:
            # From parent2 only: reduce weight
            weight = assets2[ticker]['weight'] * 0.5
            reason = assets2[ticker]['reason']

        offspring_assets.append({
            'ticker': ticker,
            'weight': weight,
            'reason': reason
        })

    # Normalize weights to sum=1.0
    total_weight = sum(a['weight'] for a in offspring_assets)
    for asset in offspring_assets:
        asset['weight'] = round(asset['weight'] / total_weight, 4)

    # Sort by weight descending
    offspring_assets.sort(key=lambda a: a['weight'], reverse=True)

    # Limit to top 15 assets to avoid bloat
    offspring_assets = offspring_assets[:15]

    # Re-normalize after trimming
    total_weight = sum(a['weight'] for a in offspring_assets)
    for asset in offspring_assets:
        asset['weight'] = round(asset['weight'] / total_weight, 4)

    offspring = {
        'generation': parent1['generation'] + 1,
        'portfolio_id': f"gen{parent1['generation'] + 1}_crossover",
        'assets': offspring_assets,
        'parents': [
            parent1.get('agent_id', 'unknown'),
            parent2.get('agent_id', 'unknown')
        ],
        'parent_fitness': [
            calculate_fitness(parent1),
            calculate_fitness(parent2)
        ]
    }

    return offspring


def mutate(portfolio: Dict, universe: List[str], mutation_rate: float = 0.15) -> Dict:
    """
    Apply random mutations to a portfolio

    Mutations:
    1. Swap 1-2 assets with random ones from universe (15% chance each)
    2. Adjust weights by ±10% (15% chance per asset)
    3. Ensure constraints still met after mutations

    Args:
        portfolio: Portfolio to mutate
        universe: List of available asset tickers
        mutation_rate: Probability of mutation (default 0.15)

    Returns:
        Mutated portfolio
    """
    mutated = json.loads(json.dumps(portfolio))  # Deep copy
    assets = mutated['assets']

    # Mutation 1: Swap random assets
    num_swaps = random.choices([0, 1, 2], weights=[0.7, 0.25, 0.05])[0]

    for _ in range(num_swaps):
        if len(assets) > 5:  # Keep at least 5
            # Remove random asset
            removed_idx = random.randint(0, len(assets) - 1)
            removed_asset = assets.pop(removed_idx)

            # Add random new asset from universe
            current_tickers = {a['ticker'] for a in assets}
            available = [t for t in universe if t not in current_tickers]

            if available:
                new_ticker = random.choice(available)
                assets.append({
                    'ticker': new_ticker,
                    'weight': removed_asset['weight'],  # Keep same weight
                    'reason': f"Mutation: replacing {removed_asset['ticker']}"
                })

    # Mutation 2: Adjust weights
    for asset in assets:
        if random.random() < mutation_rate:
            # Adjust by ±10%
            adjustment = random.uniform(-0.10, 0.10)
            asset['weight'] = max(0.01, asset['weight'] * (1 + adjustment))

    # Normalize weights
    total_weight = sum(a['weight'] for a in assets)
    for asset in assets:
        asset['weight'] = round(asset['weight'] / total_weight, 4)

    # Ensure max weight constraint (30%)
    max_weight = max(a['weight'] for a in assets)
    if max_weight > 0.30:
        # Redistribute excess
        for asset in assets:
            if asset['weight'] > 0.30:
                excess = asset['weight'] - 0.29
                asset['weight'] = 0.29
                # Distribute to others
                others = [a for a in assets if a != asset]
                for other in others:
                    other['weight'] += excess / len(others)

        # Re-normalize
        total_weight = sum(a['weight'] for a in assets)
        for asset in assets:
            asset['weight'] = round(asset['weight'] / total_weight, 4)

    mutated['portfolio_id'] = f"{portfolio['portfolio_id']}_mutated"

    return mutated


def select_best(portfolios: List[Dict], k: int = 2) -> List[Dict]:
    """
    Select top k portfolios by fitness

    Args:
        portfolios: List of portfolio dicts
        k: Number to select

    Returns:
        Top k portfolios sorted by fitness
    """
    # Calculate fitness for each
    for portfolio in portfolios:
        portfolio['fitness'] = calculate_fitness(portfolio)

    # Sort by fitness descending
    portfolios.sort(key=lambda p: p['fitness'], reverse=True)

    return portfolios[:k]


def load_asset_universe(csv_path: str = None) -> List[str]:
    """
    Load asset universe from CSV

    Args:
        csv_path: Path to CSV file or URL

    Returns:
        List of ticker symbols
    """
    if csv_path is None:
        csv_path = "https://docs.google.com/spreadsheets/d/1f3xJomL2UlCn7887jpX_MQZBsQWbmVKiQXsUdZ3kkcE/export?format=csv"

    import pandas as pd

    if csv_path.startswith('http'):
        df = pd.read_csv(csv_path)
    else:
        df = pd.read_csv(csv_path)

    # Extract tickers from column names (skip 'Date' column)
    tickers = [col for col in df.columns if col != 'Date']

    return tickers


if __name__ == '__main__':
    # Test evolution operators
    print("Testing evolution operators...")

    # Load universe
    universe = load_asset_universe()
    print(f"✅ Loaded {len(universe)} assets from universe")

    # Test portfolios
    parent1 = {
        'generation': 0,
        'agent_id': 'agent_1',
        'expected_sharpe': 1.5,
        'assets': [
            {'ticker': 'AAPL', 'weight': 0.3, 'reason': 'Tech leader'},
            {'ticker': 'MSFT', 'weight': 0.3, 'reason': 'Cloud'},
            {'ticker': 'GOOGL', 'weight': 0.2, 'reason': 'AI'},
            {'ticker': 'SPY', 'weight': 0.2, 'reason': 'Market'}
        ]
    }

    parent2 = {
        'generation': 0,
        'agent_id': 'agent_2',
        'expected_sharpe': 1.6,
        'assets': [
            {'ticker': 'NVDA', 'weight': 0.35, 'reason': 'GPU'},
            {'ticker': 'MSFT', 'weight': 0.25, 'reason': 'Azure'},
            {'ticker': 'AGG', 'weight': 0.25, 'reason': 'Bonds'},
            {'ticker': 'GLD', 'weight': 0.15, 'reason': 'Gold'}
        ]
    }

    # Test fitness
    print(f"\nFitness parent1: {calculate_fitness(parent1)}")
    print(f"Fitness parent2: {calculate_fitness(parent2)}")

    # Test crossover
    offspring = crossover(parent1, parent2)
    print(f"\n✅ Crossover created portfolio with {len(offspring['assets'])} assets")
    print(f"   Fitness: {calculate_fitness(offspring)}")

    # Test mutation
    mutated = mutate(offspring, universe, mutation_rate=0.2)
    print(f"\n✅ Mutation created portfolio with {len(mutated['assets'])} assets")
    print(f"   Fitness: {calculate_fitness(mutated)}")

    # Test selection
    all_portfolios = [parent1, parent2, offspring, mutated]
    best = select_best(all_portfolios, k=2)
    print(f"\n✅ Selection picked top 2:")
    for i, p in enumerate(best, 1):
        print(f"   {i}. {p.get('agent_id', p.get('portfolio_id'))}: {p['fitness']}")
