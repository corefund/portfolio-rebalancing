# GA Portfolio Optimization - Workflow Specification

## Overview

Genetic algorithm experiment for portfolio optimization across multiple Google Colab machines.
Coordinated by Claude Code workflow with parallel agent deployment.

## Core Files

- **program.md** - This specification document
- **program.py** - Helper utilities (not the main entry point)
- **init.sh** - Machine initialization script
- **settings.json** - Claude API configuration
- **colab_agent.py** - Portfolio generation agent
- **experiment/evolution.py** - GA operators (crossover, mutate, fitness)
- **experiment/initial_portfolio.json** - Starting portfolio for each generation

## Architecture

```
Claude Workflow (main orchestrator)
  │
  ├─ Phase 1: Initialize Machines
  │   ├─ Upload init.sh + settings.json to N machines
  │   └─ Run init.sh (installs Claude CLI, xpra, dependencies)
  │
  ├─ Phase 2-6: Generations 0-4
  │   │
  │   ├─ Deploy Generation (parallel)
  │   │   ├─ SSH to each machine
  │   │   ├─ Export env vars from settings.json
  │   │   ├─ Run colab_agent.py → generates portfolio via Claude API
  │   │   └─ Fetch result JSON via scp
  │   │
  │   ├─ Create Pull Requests (parallel)
  │   │   ├─ For each portfolio: create branch, commit, push
  │   │   └─ Create PR via gh CLI
  │   │
  │   └─ Evolution (if not last generation)
  │       ├─ Load all portfolios from generation
  │       ├─ Calculate fitness (Sharpe + diversity)
  │       ├─ Select top 2 portfolios
  │       ├─ Crossover: blend parents
  │       ├─ Mutate: random variations
  │       ├─ Save as experiment/initial_portfolio.json
  │       └─ Commit to master
  │
  └─ Phase 7: Summary
      ├─ Collect all portfolios from all generations
      ├─ Calculate statistics
      └─ Report best portfolio
```

## Machine Initialization (init.sh)

Each Colab machine needs:
1. **Claude Code CLI** - for potential orchestration
2. **Xpra** - for GUI forwarding (optional)
3. **settings.json** - API key and config
4. **Python deps** - anthropic, requests, pandas
5. **Git config** - user.name, user.email
6. **Repo clone** - portfolio-rebalancing

The `init.sh` script handles all of this automatically.

## Agent Deployment Flow

For each agent on a machine:

```bash
# 1. SSH to machine
ssh root@85.192.41.246 -p 4614

# 2. Navigate to repo
cd /content/portfolio-rebalancing
git pull origin master

# 3. Export environment
export ANTHROPIC_API_KEY="sk-..."
export ANTHROPIC_BASE_URL="https://router.plus/v1"
export ANTHROPIC_MODEL="gpt-5.5"
export AGENT_ID="agent_1"
export GENERATION="0"

# 4. Run agent
python3 colab_agent.py

# 5. Result saved to:
# /tmp/portfolio_gen0_agent_1.json
```

## Evolution Between Generations

After each generation (except last):

```python
from evolution import select_best, crossover, mutate, load_asset_universe

# Load portfolios
portfolios = [load(f) for f in glob('experiment/results/gen0_*.json')]

# Evolution
universe = load_asset_universe()
best = select_best(portfolios, k=2)
offspring = crossover(best[0], best[1])
evolved = mutate(offspring, universe, mutation_rate=0.15)

# Save for next generation
evolved['generation'] = 1
save(evolved, 'experiment/initial_portfolio.json')
```

## Portfolio Constraints

All portfolios must satisfy:
- `sum(weights) == 1.0` (±0.01 tolerance)
- `max(weight) < 0.30` (30% concentration limit)
- `5 <= len(assets) <= 20`
- All tickers from universe
- All weights > 0

Validated by `experiment/validate_portfolio.py`

## Workflow Execution

**This experiment is designed to run via Claude Code Workflow, NOT as a standalone script.**

The workflow interprets this specification and:
- Spawns sub-agents for parallel operations
- Manages SSH to Colab machines
- Handles git operations locally
- Creates PRs via gh CLI
- Generates reports

To run:
```bash
# Start Claude Code workflow that reads this specification
# The workflow will orchestrate everything automatically
```

## Configuration

**Number of agents per generation:**
- Recommended: 20 (good balance)
- Fast test: 5-10
- Thorough: 30-40 (if enough Colab sessions)

**Number of generations:**
- Standard: 5
- Quick test: 2-3
- Extended: 7-10

Edit `settings.json` for API configuration:
```json
{
  "env": {
    "ANTHROPIC_API_KEY": "sk-...",
    "ANTHROPIC_BASE_URL": "https://router.plus/v1",
    "ANTHROPIC_MODEL": "gpt-5.5"
  }
}
```

## Expected Output

For 5 generations × 20 agents:
- **100 portfolios** generated
- **100 Pull Requests** created
- **5 evolution cycles** completed
- **1 summary report** with best portfolio

All results in:
- `experiment/results/gen*_agent_*_portfolio.json`
- GitHub PRs at: https://github.com/wtf403/portfolio-rebalancing/pulls

## Success Metrics

1. ✅ All machines initialized successfully
2. ✅ >80% of agents complete per generation
3. ✅ Fitness improves across generations
4. ✅ All PRs pass validation
5. ✅ Best portfolio has Sharpe > initial

## Error Handling

- **Machine init fails**: Retry once, skip if fails again
- **Agent fails**: Log error, continue with others
- **<80% success rate**: Abort experiment
- **Evolution fails**: Use best portfolio as-is

## Asset Universe

Downloaded from Google Sheets:
https://docs.google.com/spreadsheets/d/1f3xJomL2UlCn7887jpX_MQZBsQWbmVKiQXsUdZ3kkcE/export?format=csv

Contains 1095+ stock tickers across:
- Tech (AAPL, MSFT, GOOGL, NVDA, etc.)
- Financials (JPM, BAC, GS, etc.)
- Healthcare (JNJ, PFE, UNH, etc.)
- Energy (XOM, CVX, etc.)
- ETFs (SPY, QQQ, AGG, GLD, etc.)
- Crypto (BTC-USD, ETH-USD, etc.)

## Next Steps

To start the experiment, a Claude Code workflow should:
1. Read this program.md specification
2. Get available Colab sessions via `colab sessions`
3. Initialize N machines in parallel
4. Run the generation loop as specified
5. Generate final report

The workflow implementation would use the `Workflow` tool with phases matching this specification.
