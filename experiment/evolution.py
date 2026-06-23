#!/usr/bin/env python3
"""
Genetic Algorithm evolution operators for portfolio optimization
"""

import random
import json
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from pathlib import Path


def load_historical_data(csv_path: str = None) -> pd.DataFrame:
    """
    Load historical price data

    Args:
        csv_path: Path to CSV file or URL

    Returns:
        DataFrame with Date index and ticker columns
    """
    if csv_path is None:
        csv_path = "https://docs.google.com/spreadsheets/d/1f3xJomL2UlCn7887jpX_MQZBsQWbmVKiQXsUdZ3kkcE/export?format=csv"

    df = pd.read_csv(csv_path)
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)

    return df


def calculate_portfolio_returns(portfolio: Dict, prices: pd.DataFrame) -> pd.Series:
    """
    Calculate daily portfolio returns based on weights

    Args:
        portfolio: Portfolio with assets and weights
        prices: Historical price DataFrame

    Returns:
        Series of daily portfolio returns
    """
    # Calculate daily returns for each asset
    returns = prices.pct_change().dropna()

    # Get portfolio weights
    weights = {}
    for asset in portfolio['assets']:
        ticker = asset['ticker']
        if ticker in returns.columns:
            weights[ticker] = asset['weight']

    # Calculate weighted portfolio returns
    portfolio_returns = pd.Series(0.0, index=returns.index)

    for ticker, weight in weights.items():
        if ticker in returns.columns:
            portfolio_returns += returns[ticker] * weight

    return portfolio_returns


def calculate_metrics(returns: pd.Series, risk_free_rate: float = 0.0) -> Dict[str, float]:
    """
    Calculate all performance metrics for portfolio returns

    Args:
        returns: Series of daily returns
        risk_free_rate: Annual risk-free rate (default 0.0)

    Returns:
        Dict with all metrics
    """
    if len(returns) == 0 or returns.std() == 0:
        return {
            'sharpe': 0.0,
            'sortino': 0.0,
            'calmar': 0.0,
            'cagr': 0.0,
            'total_return': 0.0,
            'volatility': 0.0,
            'max_drawdown': 0.0,
            'alpha': 0.0,
            'beta': 1.0
        }

    # Annualization factor (252 trading days)
    annual_factor = 252

    # 1. Sharpe Ratio
    mean_return = returns.mean()
    std_return = returns.std()
    sharpe = (mean_return * annual_factor - risk_free_rate) / (std_return * np.sqrt(annual_factor))

    # 2. Sortino Ratio (downside deviation)
    downside_returns = returns[returns < 0]
    downside_std = downside_returns.std() if len(downside_returns) > 0 else std_return
    sortino = (mean_return * annual_factor - risk_free_rate) / (downside_std * np.sqrt(annual_factor))

    # 3. Max Drawdown
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.expanding().max()
    drawdown = (cumulative - running_max) / running_max
    max_drawdown = abs(drawdown.min())

    # 4. Calmar Ratio
    calmar = (mean_return * annual_factor) / max_drawdown if max_drawdown > 0 else 0.0

    # 5. CAGR (Compound Annual Growth Rate)
    total_return = cumulative.iloc[-1] - 1
    years = len(returns) / annual_factor
    cagr = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0.0

    # 6. Total Return
    total_return = cumulative.iloc[-1] - 1

    # 7. Volatility (annualized)
    volatility = std_return * np.sqrt(annual_factor)

    # 8. Alpha and Beta (simplified, using market proxy if available)
    # For now, use simplified estimates
    alpha = mean_return * annual_factor - risk_free_rate  # Excess return
    beta = 1.0  # Placeholder

    return {
        'sharpe': float(sharpe),
        'sortino': float(sortino),
        'calmar': float(calmar),
        'cagr': float(cagr),
        'total_return': float(total_return),
        'volatility': float(volatility),
        'max_drawdown': float(max_drawdown),
        'alpha': float(alpha),
        'beta': float(beta)
    }


def calculate_fitness(portfolio: Dict, prices: Optional[pd.DataFrame] = None) -> float:
    """
    Calculate fitness score using comprehensive metrics

    Fitness = 0.35×Sharpe + 0.20×Sortino + 0.15×Calmar + 0.15×CAGR
              + 0.10×TotalReturn - 0.10×Volatility - 0.10×MaxDrawdown
              + 0.05×Alpha - 0.05×Beta

    Args:
        portfolio: Portfolio dict with assets and weights
        prices: Historical price DataFrame (loaded once and cached)

    Returns:
        Float fitness score (higher is better)
    """
    # If prices not provided, try to use cached or load
    if prices is None:
        if not hasattr(calculate_fitness, '_prices_cache'):
            calculate_fitness._prices_cache = load_historical_data()
        prices = calculate_fitness._prices_cache

    # Calculate portfolio returns
    returns = calculate_portfolio_returns(portfolio, prices)

    # Calculate all metrics
    metrics = calculate_metrics(returns)

    # Store metrics in portfolio for logging
    portfolio['metrics'] = metrics

    # Apply fitness formula
    fitness = (
        0.35 * metrics['sharpe'] +
        0.20 * metrics['sortino'] +
        0.15 * metrics['calmar'] +
        0.15 * metrics['cagr'] +
        0.10 * metrics['total_return'] -
        0.10 * metrics['volatility'] -
        0.10 * metrics['max_drawdown'] +
        0.05 * metrics['alpha'] -
        0.05 * metrics['beta']
    )

    return round(fitness, 4)


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


def select_best(portfolios: List[Dict], k: int = 2, prices: Optional[pd.DataFrame] = None) -> List[Dict]:
    """
    Select top k portfolios by fitness

    Args:
        portfolios: List of portfolio dicts
        k: Number to select
        prices: Historical price DataFrame (optional, will be cached)

    Returns:
        Top k portfolios sorted by fitness
    """
    # Load prices once for all portfolios
    if prices is None:
        prices = load_historical_data()

    # Calculate fitness for each
    for portfolio in portfolios:
        portfolio['fitness'] = calculate_fitness(portfolio, prices)

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

    # Load historical data
    print("Loading historical data...")
    prices = load_historical_data()
    print(f"✅ Loaded {len(prices)} days of data for {len(prices.columns)} assets")

    # Load universe
    universe = load_asset_universe()
    print(f"✅ Loaded {len(universe)} assets from universe")

    # Test portfolios
    parent1 = {
        'generation': 0,
        'agent_id': 'agent_1',
        'assets': [
            {'ticker': 'SPY', 'weight': 0.25, 'reason': 'S&P 500'},
            {'ticker': 'QQQ', 'weight': 0.20, 'reason': 'Tech'},
            {'ticker': 'AGG', 'weight': 0.20, 'reason': 'Bonds'},
            {'ticker': 'GLD', 'weight': 0.15, 'reason': 'Gold'},
            {'ticker': 'VNQ', 'weight': 0.20, 'reason': 'Real Estate'}
        ]
    }

    parent2 = {
        'generation': 0,
        'agent_id': 'agent_2',
        'assets': [
            {'ticker': 'AAPL', 'weight': 0.20, 'reason': 'Tech leader'},
            {'ticker': 'MSFT', 'weight': 0.20, 'reason': 'Cloud'},
            {'ticker': 'GOOGL', 'weight': 0.15, 'reason': 'AI'},
            {'ticker': 'SPY', 'weight': 0.25, 'reason': 'Market'},
            {'ticker': 'AGG', 'weight': 0.20, 'reason': 'Bonds'}
        ]
    }

    # Test fitness with real metrics
    print(f"\nCalculating fitness for parent1...")
    fitness1 = calculate_fitness(parent1, prices)
    print(f"✅ Fitness: {fitness1}")
    if 'metrics' in parent1:
        m = parent1['metrics']
        print(f"   Sharpe: {m['sharpe']:.3f}, Sortino: {m['sortino']:.3f}, Calmar: {m['calmar']:.3f}")
        print(f"   CAGR: {m['cagr']:.2%}, MaxDD: {m['max_drawdown']:.2%}, Vol: {m['volatility']:.2%}")

    print(f"\nCalculating fitness for parent2...")
    fitness2 = calculate_fitness(parent2, prices)
    print(f"✅ Fitness: {fitness2}")
    if 'metrics' in parent2:
        m = parent2['metrics']
        print(f"   Sharpe: {m['sharpe']:.3f}, Sortino: {m['sortino']:.3f}, Calmar: {m['calmar']:.3f}")
        print(f"   CAGR: {m['cagr']:.2%}, MaxDD: {m['max_drawdown']:.2%}, Vol: {m['volatility']:.2%}")

    # Test crossover
    offspring = crossover(parent1, parent2)
    print(f"\n✅ Crossover created portfolio with {len(offspring['assets'])} assets")
    offspring_fitness = calculate_fitness(offspring, prices)
    print(f"   Fitness: {offspring_fitness}")

    # Test mutation
    mutated = mutate(offspring, universe, mutation_rate=0.2)
    print(f"\n✅ Mutation created portfolio with {len(mutated['assets'])} assets")
    mutated_fitness = calculate_fitness(mutated, prices)
    print(f"   Fitness: {mutated_fitness}")

    # Test selection
    all_portfolios = [parent1, parent2, offspring, mutated]
    best = select_best(all_portfolios, k=2, prices=prices)
    print(f"\n✅ Selection picked top 2:")
    for i, p in enumerate(best, 1):
        print(f"   {i}. {p.get('agent_id', p.get('portfolio_id'))}: {p['fitness']:.4f}")
