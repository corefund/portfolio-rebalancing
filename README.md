# GA Portfolio Optimization Experiment

Genetic algorithm experiment for portfolio optimization using distributed Claude agents across Google Colab machines.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Main Workflow Orchestrator               │
│                  (ga_experiment.workflow.js)                │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
   ┌────▼────┐    ┌───▼────┐    ┌───▼────┐
   │ Colab 1 │    │ Colab 2│    │ Colab N│
   │ Agent 1 │    │ Agent 2│    │ Agent N│
   └────┬────┘    └───┬────┘    └───┬────┘
        │             │              │
        └─────────────┼──────────────┘
                      │
              ┌───────▼────────┐
              │   Evolution    │
              │ (best parents) │
              └───────┬────────┘
                      │
              Next Generation
```

## Components

### Core Files

- **ga_experiment.workflow.js** — Main workflow orchestrator
- **colab_agent.py** — Portfolio generation agent (runs on Colab)
- **experiment/evolution.py** — GA operators (fitness, crossover, mutation)
- **experiment/validate_portfolio.py** — Portfolio validation
- **experiment/agent_prompt.md** — Instructions for portfolio agents
- **experiment/initial_portfolio.json** — Starting portfolio (updated each gen)
- **init.sh** — Machine initialization script
- **settings.json** — API configuration

### Helper Scripts

- **test_agent.sh** — Test agent locally
- **program.py** — Legacy utilities
- **program.md** — Original specification

## Quick Start

### Option 1: Run Full Workflow

```bash
# Run complete GA experiment (5 generations × 20 agents)
# Requires ultracode mode enabled
```

Workflow will automatically:
1. Get available Colab sessions
2. Initialize machines in parallel
3. Run 5 generations with evolution
4. Generate final report

### Option 2: Test Single Agent Locally

```bash
./test_agent.sh
```

### Option 3: Manual Deployment

```bash
# 1. Get Colab sessions
colab sessions

# 2. Initialize a machine
ssh root@85.192.41.246 -p <PORT>
cd /content && bash init.sh

# 3. Run agent
export AGENT_ID="agent_1"
export GENERATION="0"
export ANTHROPIC_API_KEY="..."
python3 colab_agent.py

# 4. Fetch result
scp root@85.192.41.246:<PORT>:/tmp/portfolio_gen0_agent_1.json .
```

## Fitness Function

Comprehensive 9-metric formula:

```
Fitness = 0.35×Sharpe + 0.20×Sortino + 0.15×Calmar + 0.15×CAGR
        + 0.10×TotalReturn - 0.10×Volatility - 0.10×MaxDrawdown
        + 0.05×Alpha - 0.05×Beta
```

Calculated on 730 days of historical data across 1095 assets.

## Portfolio Constraints

- Total weight = 1.0 (±0.01 tolerance)
- Per-asset weight: 5% - 25%
- Number of assets: 8-12
- All tickers from universe
- Diversified across asset classes

## Evolution Process

Each generation:
1. **Deploy** — 20 agents generate portfolios in parallel
2. **Evaluate** — Calculate fitness using historical data
3. **Select** — Pick top 2 parents
4. **Crossover** — Blend parent portfolios
5. **Mutate** — Random variations (15% rate)
6. **Save** — New initial portfolio for next generation

## Output

Results stored in:
- `experiment/results/gen{N}_agent_{M}_portfolio.json`
- Each portfolio includes:
  - Assets with weights and reasons
  - Calculated fitness metrics
  - Generation and parent information

Pull requests created automatically for each portfolio with full validation.

## Configuration

Edit `settings.json`:

```json
{
  "env": {
    "ANTHROPIC_API_KEY": "your-key",
    "ANTHROPIC_BASE_URL": "https://router.plus/v1",
    "ANTHROPIC_MODEL": "gpt-5.5"
  }
}
```

Workflow parameters:
- `args.agents` — Agents per generation (default: 20)
- `NUM_GENERATIONS` — Number of generations (default: 5)

## Monitoring

Use `/workflows` command to watch live progress:
- Phase completion
- Agent success rate
- Evolution results
- Final summary

## Asset Universe

1095+ tickers across:
- **Tech**: AAPL, MSFT, GOOGL, NVDA, META, TSLA...
- **Finance**: JPM, BAC, GS, WFC, MS...
- **Healthcare**: JNJ, PFE, UNH, ABBV...
- **Energy**: XOM, CVX, COP, SLB...
- **ETFs**: SPY, QQQ, AGG, GLD, VNQ, TLT...
- **Crypto**: BTC-USD, ETH-USD...

Source: [Google Sheets CSV](https://docs.google.com/spreadsheets/d/1f3xJomL2UlCn7887jpX_MQZBsQWbmVKiQXsUdZ3kkcE/export?format=csv)

## Error Handling

- Machine init fails → Retry once, skip if still fails
- Agent fails → Log error, continue with others
- <80% success rate → Abort experiment
- Evolution fails → Use best portfolio as-is

## Success Metrics

1. ✅ All machines initialized successfully
2. ✅ >80% of agents complete per generation
3. ✅ Fitness improves across generations
4. ✅ All PRs pass validation
5. ✅ Best portfolio has higher fitness than initial

## Expected Results

For 5 generations × 20 agents:
- **100 portfolios** generated
- **100 Pull Requests** created (if enabled)
- **5 evolution cycles** completed
- **1 comprehensive report** with best portfolio

Typical fitness progression:
- Gen 0: 1.5 - 3.0 (random variation)
- Gen 4: 3.0 - 6.0 (evolved optimization)

## Troubleshooting

**"No Colab sessions available"**
- Start more Colab notebooks
- Use smaller `args.agents` value

**"Agent timeout"**
- Check API key validity
- Verify network connectivity on Colab
- Increase timeout in workflow

**"Evolution fails"**
- Check historical data availability
- Verify pandas/numpy installed
- Review evolution.py for errors

**"Validation fails"**
- Check portfolio constraints
- Verify ticker symbols exist in universe
- Review weight calculations

## Contributing

To improve the experiment:
1. Tune fitness function weights in `evolution.py`
2. Adjust mutation rate and strategy
3. Modify crossover blending logic
4. Add new optimization metrics
5. Enhance agent prompts

## Current Status

- ✅ Fitness function: 9-metric comprehensive formula
- ✅ Workflow: Full orchestration with parallel execution
- ✅ Validation: Automated with GitHub Actions
- ✅ Evolution: Crossover + mutation operators
- 🚀 Experiment: Running in ultracode mode

## License

MIT
