"""
Portfolio GA Strategy - Agent editable file
Modify this file to improve portfolio performance.
"""

import numpy as np
from prepare import run_backtest, BENCHMARK_CONFIG

# ---------------------------------------------------------------------------
# Chromosome Encoding
# ---------------------------------------------------------------------------

class Chromosome:
    """
    Genome encoding for portfolio strategy.

    Representation:
    - selection_scores: [n_assets] float array for asset selection
    - allocation_logits: [n_assets] float array for weight allocation
    - top_k: number of assets to select
    - rebalance_threshold: drift threshold to trigger rebalance
    """

    def __init__(self, universe):
        self.universe = universe
        n = len(universe)

        # Initialize with random values
        self.selection_scores = np.random.randn(n) * 0.1
        self.allocation_logits = np.random.randn(n) * 0.1
        self.top_k = 12  # Select at least 12 assets for diversification
        self.rebalance_threshold = 0.05

    def decode_weights(self):
        """Convert chromosome to portfolio weights."""
        # Select top-k assets by selection scores
        top_indices = np.argsort(self.selection_scores)[-self.top_k:]

        # Allocate weights via softmax on allocation logits
        logits = self.allocation_logits[top_indices]
        weights = np.exp(logits) / np.exp(logits).sum()

        # Build full weight vector
        full_weights = np.zeros(len(self.universe))
        full_weights[top_indices] = weights

        return full_weights

    def to_dict(self):
        return {
            'selection_scores': self.selection_scores.tolist(),
            'allocation_logits': self.allocation_logits.tolist(),
            'top_k': self.top_k,
            'rebalance_threshold': self.rebalance_threshold,
        }

# ---------------------------------------------------------------------------
# GA Operators
# ---------------------------------------------------------------------------

def mutate(chromosome, rate=0.1):
    """Gaussian mutation on scores and logits."""
    n = len(chromosome.selection_scores)

    # Mutate selection scores
    mask = np.random.rand(n) < rate
    chromosome.selection_scores[mask] += np.random.randn(mask.sum()) * 0.1

    # Mutate allocation logits
    mask = np.random.rand(n) < rate
    chromosome.allocation_logits[mask] += np.random.randn(mask.sum()) * 0.1

    # Occasionally mutate top_k
    if np.random.rand() < 0.1:
        chromosome.top_k = max(3, min(8, chromosome.top_k + np.random.choice([-1, 0, 1])))

    # Occasionally mutate rebalance threshold
    if np.random.rand() < 0.1:
        chromosome.rebalance_threshold = max(0.01, min(0.20,
            chromosome.rebalance_threshold + np.random.randn() * 0.01))

    return chromosome

def crossover(parent1, parent2):
    """Uniform crossover between two chromosomes."""
    child = Chromosome(parent1.universe)
    n = len(parent1.selection_scores)

    # Blend selection scores
    alpha = np.random.rand(n)
    child.selection_scores = alpha * parent1.selection_scores + (1 - alpha) * parent2.selection_scores

    # Blend allocation logits
    alpha = np.random.rand(n)
    child.allocation_logits = alpha * parent1.allocation_logits + (1 - alpha) * parent2.allocation_logits

    # Inherit discrete params from random parent
    child.top_k = np.random.choice([parent1.top_k, parent2.top_k])
    child.rebalance_threshold = np.random.choice([parent1.rebalance_threshold, parent2.rebalance_threshold])

    return child

# ---------------------------------------------------------------------------
# Rebalance Logic
# ---------------------------------------------------------------------------

def should_rebalance(current_weights, target_weights, threshold):
    """Check if portfolio drift exceeds threshold."""
    drift = np.abs(current_weights - target_weights).sum()
    return drift > threshold

def generate_trades(current_weights, target_weights, portfolio_value):
    """Generate trade list from weight changes."""
    trades = []
    for i, (curr, tgt) in enumerate(zip(current_weights, target_weights)):
        delta = tgt - curr
        if abs(delta) > 1e-6:
            trades.append({
                'asset_idx': i,
                'delta_weight': delta,
                'dollar_amount': delta * portfolio_value
            })
    return trades

# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    # Create initial chromosome
    universe = BENCHMARK_CONFIG['universe']
    chromosome = Chromosome(universe)

    # Run backtest (calls locked evaluation in prepare.py)
    result = run_backtest(chromosome)

    # Print results in standard format
    print(f"---")
    print(f"composite_score:  {result['composite_score']:.6f}")
    print(f"sharpe:           {result['sharpe']:.4f}")
    print(f"sortino:          {result['sortino']:.4f}")
    print(f"cagr:             {result['cagr']:.4f}")
    print(f"max_drawdown:     {result['max_drawdown']:.4f}")
    print(f"turnover:         {result['turnover']:.4f}")
    print(f"volatility:       {result['volatility']:.4f}")
    print(f"rp_loss:          {result['rp_loss']:.4f}")
