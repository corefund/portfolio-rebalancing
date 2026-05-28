"""
Locked evaluation harness - DO NOT MODIFY
Contains benchmark config, data loading, and fitness function.
"""

import numpy as np
import pandas as pd
import yfinance as yf
import os
import urllib.request
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Universe Loading
# ---------------------------------------------------------------------------

def load_universe():
    """
    Load asset universe from CSV source.

    Priority:
    1. Local universe.csv if exists
    2. Download from UNIVERSE_URL env var if set
    3. Fall back to default universe
    """
    # Check for local universe.csv
    if os.path.exists('universe.csv'):
        df = pd.read_csv('universe.csv')
        if 'ticker' in df.columns:
            return df['ticker'].dropna().tolist()
        elif 'symbol' in df.columns:
            return df['symbol'].dropna().tolist()
        else:
            # Assume first column is tickers
            return df.iloc[:, 0].dropna().tolist()

    # Try to download from URL
    universe_url = os.getenv('UNIVERSE_URL')
    if universe_url:
        try:
            urllib.request.urlretrieve(universe_url, 'universe_temp.csv')
            df = pd.read_csv('universe_temp.csv')

            # Check if this is a returns CSV (has 'date' columns and ticker columns)
            # Extract tickers from column names, excluding 'date' and empty columns
            if 'date' in df.columns or any('date' in str(col).lower() for col in df.columns):
                tickers = [col for col in df.columns
                          if col and 'date' not in str(col).lower()
                          and not str(col).startswith('Unnamed')
                          and not any(x in str(col) for x in ['Algotoria', 'Quantum', 'Basket', 'BTC', 'USDT'])]
                if tickers:
                    os.remove('universe_temp.csv')
                    # Filter to only valid ticker symbols (uppercase, 2-5 chars)
                    valid_tickers = [t for t in tickers if t.isupper() and 2 <= len(t) <= 5]
                    return sorted(set(valid_tickers))

            # Otherwise treat as ticker list
            if 'ticker' in df.columns:
                tickers = df['ticker'].dropna().tolist()
            elif 'symbol' in df.columns:
                tickers = df['symbol'].dropna().tolist()
            else:
                tickers = df.iloc[:, 0].dropna().tolist()

            os.remove('universe_temp.csv')
            return tickers
        except Exception as e:
            print(f"Warning: Failed to download universe from {universe_url}: {e}")
            print("Falling back to default universe")

    # Default universe
    return ['SPY', 'TLT', 'GLD', 'VNQ', 'DBC', 'VEA', 'VWO', 'AGG']

# ---------------------------------------------------------------------------
# Benchmark Configuration (LOCKED)
# ---------------------------------------------------------------------------

BENCHMARK_CONFIG = {
    'universe': load_universe(),
    'train_start': '2010-01-01',
    'train_end': '2018-12-31',
    'val_start': '2019-01-01',
    'val_end': '2021-12-31',
    'test_start': '2022-01-01',
    'test_end': '2024-12-31',
    'starting_capital': 100000,
    'transaction_cost_bps': 5,
}

# ---------------------------------------------------------------------------
# Data Loading
# ---------------------------------------------------------------------------

def fetch_prices(tickers, start_date, end_date):
    """Fetch historical prices from yfinance."""
    data = yf.download(tickers, start=start_date, end=end_date, progress=False)

    if len(tickers) == 1:
        # Single ticker returns simple DataFrame
        if 'Close' in data.columns:
            prices = data['Close'].to_frame()
        else:
            prices = data
        prices.columns = tickers
    else:
        # Multiple tickers return MultiIndex DataFrame
        if isinstance(data.columns, pd.MultiIndex):
            # Extract 'Close' prices for all tickers
            prices = data['Close']
        else:
            prices = data

    return prices.ffill().dropna()

# ---------------------------------------------------------------------------
# Fitness Function (LOCKED)
# ---------------------------------------------------------------------------

def evaluate_portfolio(weights_history, returns, turnover):
    """
    Compute fitness metrics for a portfolio.

    Args:
        weights_history: [T, n_assets] array of portfolio weights over time
        returns: [T, n_assets] array of asset returns
        turnover: float, average turnover per rebalance

    Returns:
        dict with metrics and composite score
    """
    # Portfolio returns
    portfolio_returns = (weights_history[:-1] * returns[1:]).sum(axis=1)

    # Cumulative return
    cum_returns = (1 + portfolio_returns).cumprod()
    total_return = cum_returns[-1] - 1

    # CAGR
    n_years = len(portfolio_returns) / 252
    cagr = (1 + total_return) ** (1 / n_years) - 1

    # Volatility (annualized)
    volatility = portfolio_returns.std() * np.sqrt(252)

    # Sharpe ratio (assume 0% risk-free rate)
    sharpe = (portfolio_returns.mean() * 252) / (volatility + 1e-8)

    # Sortino ratio (downside deviation)
    downside_returns = portfolio_returns[portfolio_returns < 0]
    downside_std = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else volatility
    sortino = (portfolio_returns.mean() * 252) / (downside_std + 1e-8)

    # Max drawdown
    cum_max = np.maximum.accumulate(cum_returns)
    drawdowns = (cum_returns - cum_max) / cum_max
    max_drawdown = drawdowns.min()

    # Risk parity loss (deviation from equal risk contribution)
    avg_weights = weights_history.mean(axis=0)
    asset_vols = returns.std(axis=0) * np.sqrt(252)
    risk_contributions = avg_weights * asset_vols
    risk_contributions = risk_contributions / (risk_contributions.sum() + 1e-8)
    target_risk = 1.0 / len(avg_weights)
    rp_loss = ((risk_contributions - target_risk) ** 2).sum()

    # Composite score (LOCKED FORMULA)
    composite_score = (
        0.30 * sharpe +
        0.20 * sortino +
        0.15 * cagr -
        0.15 * abs(max_drawdown) -
        0.10 * volatility -
        0.05 * turnover -
        0.05 * rp_loss
    )

    return {
        'composite_score': composite_score,
        'sharpe': sharpe,
        'sortino': sortino,
        'cagr': cagr,
        'max_drawdown': max_drawdown,
        'volatility': volatility,
        'turnover': turnover,
        'rp_loss': rp_loss,
        'total_return': total_return,
    }

# ---------------------------------------------------------------------------
# Backtest Runner (LOCKED)
# ---------------------------------------------------------------------------

def run_backtest(chromosome, split='val'):
    """
    Run backtest on specified split (train/val/test).
    This is the locked evaluation harness.
    """
    config = BENCHMARK_CONFIG

    # Select date range
    if split == 'train':
        start, end = config['train_start'], config['train_end']
    elif split == 'val':
        start, end = config['val_start'], config['val_end']
    else:  # test
        start, end = config['test_start'], config['test_end']

    # Fetch price data
    prices = fetch_prices(config['universe'], start, end)
    returns = prices.pct_change().fillna(0).values

    # Initialize portfolio
    T = len(prices)
    n_assets = len(config['universe'])
    weights_history = np.zeros((T, n_assets))
    portfolio_value = config['starting_capital']

    # Get target weights from chromosome
    target_weights = chromosome.decode_weights()
    current_weights = target_weights.copy()
    weights_history[0] = current_weights

    # Track turnover
    total_turnover = 0
    n_rebalances = 0

    # Simulate portfolio
    for t in range(1, T):
        # Update weights due to price changes (drift)
        current_weights = current_weights * (1 + returns[t])
        current_weights = current_weights / (current_weights.sum() + 1e-8)

        # Check if rebalance needed
        from strategy import should_rebalance
        if should_rebalance(current_weights, target_weights, chromosome.rebalance_threshold):
            # Compute turnover (sum of absolute weight changes)
            turnover = np.abs(current_weights - target_weights).sum()
            total_turnover += turnover
            n_rebalances += 1

            # Apply transaction costs
            cost = turnover * config['transaction_cost_bps'] / 10000
            portfolio_value *= (1 - cost)

            # Rebalance to target
            current_weights = target_weights.copy()

        weights_history[t] = current_weights

    # Compute average turnover per rebalance
    avg_turnover = total_turnover / max(n_rebalances, 1)

    # Evaluate fitness
    metrics = evaluate_portfolio(weights_history, returns, avg_turnover)

    return metrics
