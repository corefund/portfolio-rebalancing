#!/usr/bin/env node
/**
 * GA Portfolio Optimization Experiment - Production Workflow
 *
 * Runs 5 generations of genetic algorithm across Colab machines
 * All git operations happen locally, Colab machines only generate portfolios
 */

export const meta = {
  name: 'ga-portfolio-experiment',
  description: 'Run 5-generation GA experiment across Colab machines',
  phases: [
    { title: 'Setup', detail: 'Load universe, get Colab sessions' },
    { title: 'Init Machines', detail: 'Run init.sh on all machines' },
    { title: 'Gen 0', detail: '20 agents generate portfolios' },
    { title: 'PRs Gen 0', detail: 'Create 20 Pull Requests locally' },
    { title: 'Evolve 0→1', detail: 'Select, crossover, mutate' },
    { title: 'Gen 1', detail: '20 agents with evolved portfolio' },
    { title: 'PRs Gen 1', detail: 'Create 20 Pull Requests' },
    { title: 'Evolve 1→2', detail: 'Select, crossover, mutate' },
    { title: 'Gen 2', detail: '20 agents' },
    { title: 'PRs Gen 2', detail: 'Create 20 Pull Requests' },
    { title: 'Evolve 2→3', detail: 'Select, crossover, mutate' },
    { title: 'Gen 3', detail: '20 agents' },
    { title: 'PRs Gen 3', detail: 'Create 20 Pull Requests' },
    { title: 'Evolve 3→4', detail: 'Select, crossover, mutate' },
    { title: 'Gen 4', detail: '20 agents (final)' },
    { title: 'PRs Gen 4', detail: 'Create 20 Pull Requests' },
    { title: 'Summary', detail: 'Generate experiment report' }
  ]
}

// ============================================================================
// PHASE 1: SETUP
// ============================================================================

phase('Setup')
log('🚀 GA Portfolio Optimization Experiment')
log('   5 generations × 20 agents = 100 portfolios')

// Get Colab sessions
log('📡 Getting Colab sessions...')
const sessions_output = await agent(
  `Run command: colab sessions | grep "SSH:" | sed 's/.*SSH: //' | head -65

  Return array of SSH connection strings.`,
  {
    label: 'Get sessions',
    effort: 'low'
  }
)

const all_sessions = sessions_output.split('\n').filter(s => s.trim().startsWith('ssh'))
const NUM_AGENTS = 20
const sessions = all_sessions.slice(0, NUM_AGENTS)

log(`✅ Found ${all_sessions.length} sessions, using ${NUM_AGENTS}`)

// Load asset universe
log('📊 Loading asset universe...')
const universe_csv = await agent(
  `Download CSV: https://docs.google.com/spreadsheets/d/1f3xJomL2UlCn7887jpX_MQZBsQWbmVKiQXsUdZ3kkcE/export?format=csv

  Parse header, return list of tickers (skip Date column).
  Return as comma-separated string.`,
  {
    label: 'Load universe',
    effort: 'low'
  }
)

log(`✅ Asset universe: ${universe_csv.split(',').length} tickers`)

// Read API config from settings.json
log('⚙️  Reading API configuration...')
const config = await agent(
  `Read settings.json and return:
  - ANTHROPIC_API_KEY
  - ANTHROPIC_BASE_URL
  - ANTHROPIC_MODEL`,
  {
    label: 'Read config',
    effort: 'low'
  }
)

log('✅ Configuration loaded')

// ============================================================================
// PHASE 2: INITIALIZE MACHINES
// ============================================================================

phase('Init Machines')
log(`🔧 Initializing ${NUM_AGENTS} Colab machines...`)

const init_tasks = sessions.map((ssh, i) => async () => {
  const agent_num = i + 1

  return agent(
    `Initialize Colab machine for agent ${agent_num}.

SSH: ${ssh}

Tasks:
1. scp init.sh settings.json to machine:
   HOST_PORT=\$(echo "${ssh}" | sed 's/ssh //')
   scp -o StrictHostKeyChecking=no init.sh settings.json \$HOST_PORT:/content/

2. SSH and run init.sh:
   ${ssh} << 'EOF'
cd /content
bash init.sh
EOF

3. Verify initialization:
   ${ssh} "cd /content/portfolio-rebalancing && git status && python3 -c 'import anthropic; print(\"OK\")'"

Return: { success: true, agent: ${agent_num}, ssh: "${ssh}" } if OK
        { success: false, error: "..." } if failed`,
    {
      label: `Init agent ${agent_num}`,
      phase: 'Init Machines',
      effort: 'low'
    }
  )
})

const init_results = await parallel(init_tasks)
const initialized = init_results.filter(r => r && r.success).length

log(`✅ Initialized ${initialized}/${NUM_AGENTS} machines`)

if (initialized < NUM_AGENTS * 0.7) {
  log(`❌ Too many failures (${initialized}/${NUM_AGENTS}), aborting`)
  return { error: 'Initialization failed', initialized }
}

// ============================================================================
// HELPER: Deploy Generation
// ============================================================================

async function deployGeneration(gen) {
  phase(`Gen ${gen}`)
  log(`📡 Generation ${gen}: Deploying ${NUM_AGENTS} agents...`)

  // Read current portfolio
  const current_portfolio = await agent(
    `Read experiment/initial_portfolio.json and return JSON content`,
    {
      label: 'Read portfolio',
      effort: 'low'
    }
  )

  // Deploy all agents in parallel
  const deploy_tasks = sessions.slice(0, NUM_AGENTS).map((ssh, i) => async () => {
    const agent_id = `agent_${i + 1}`

    return agent(
      `Deploy agent ${agent_id} on Colab machine for Generation ${gen}.

SSH: ${ssh}

Steps:
1. SSH to machine and run:

${ssh} << 'REMOTE_EOF'
set -e
cd /content/portfolio-rebalancing
git pull origin master

# Export environment
export ANTHROPIC_API_KEY="${config.ANTHROPIC_API_KEY}"
export ANTHROPIC_BASE_URL="${config.ANTHROPIC_BASE_URL}"
export ANTHROPIC_MODEL="${config.ANTHROPIC_MODEL}"
export AGENT_ID="${agent_id}"
export GENERATION="${gen}"

# Write current portfolio
cat > experiment/initial_portfolio.json << 'PORTFOLIO_EOF'
${JSON.stringify(current_portfolio, null, 2)}
PORTFOLIO_EOF

# Run agent
python3 colab_agent.py

echo "DONE: /tmp/portfolio_gen${gen}_${agent_id}.json"
REMOTE_EOF

2. Check if portfolio was generated:
   ${ssh} "ls -lh /tmp/portfolio_gen${gen}_${agent_id}.json"

3. Fetch portfolio locally:
   HOST_PORT=\$(echo "${ssh}" | sed 's/ssh //')
   mkdir -p experiment/results
   scp -o StrictHostKeyChecking=no \$HOST_PORT:/tmp/portfolio_gen${gen}_${agent_id}.json experiment/results/gen${gen}_${agent_id}_portfolio.json

4. Return fetched portfolio JSON content from experiment/results/gen${gen}_${agent_id}_portfolio.json

If any step fails, return null.`,
      {
        label: agent_id,
        phase: `Gen ${gen}`,
        effort: 'medium'
      }
    )
  })

  const portfolios = await parallel(deploy_tasks)
  const successful = portfolios.filter(Boolean)

  log(`✅ Gen ${gen}: ${successful.length}/${NUM_AGENTS} portfolios generated`)

  return successful
}

// ============================================================================
// HELPER: Create PRs
// ============================================================================

async function createPRs(gen, portfolios) {
  phase(`PRs Gen ${gen}`)
  log(`📨 Creating ${portfolios.length} Pull Requests...`)

  for (const portfolio of portfolios) {
    if (!portfolio || !portfolio.agent_id) continue

    await agent(
      `Create Pull Request for ${portfolio.agent_id} Generation ${gen}.

Portfolio: ${JSON.stringify(portfolio, null, 2)}

Steps:
1. Create branch:
   git checkout master
   git pull origin master
   git checkout -b gen${gen}_${portfolio.agent_id}

2. Portfolio already in experiment/results/gen${gen}_${portfolio.agent_id}_portfolio.json
   git add experiment/results/gen${gen}_${portfolio.agent_id}_portfolio.json

3. Commit:
   git commit -m "[Gen ${gen}] ${portfolio.agent_id}: Sharpe ${portfolio.expected_sharpe || 'N/A'}

Machine: ${portfolio.machine_info?.ip || 'unknown'}
Assets: ${portfolio.assets?.length || 0}"

4. Push:
   git push -u origin gen${gen}_${portfolio.agent_id}

5. Create PR:
   gh pr create --title "[Gen ${gen}] Portfolio by ${portfolio.agent_id}" --body "**Generation:** ${gen}
**Agent:** ${portfolio.agent_id}
**Expected Sharpe:** ${portfolio.expected_sharpe || 'N/A'}
**Machine IP:** ${portfolio.machine_info?.ip || 'unknown'}

### Assets
$(jq '.assets' experiment/results/gen${gen}_${portfolio.agent_id}_portfolio.json)

*Generated via GA experiment*" --base master --head gen${gen}_${portfolio.agent_id}

6. Return to master:
   git checkout master

Return PR URL or "created"`,
      {
        label: `PR ${portfolio.agent_id}`,
        phase: `PRs Gen ${gen}`,
        effort: 'low'
      }
    )
  }

  log(`✅ Created ${portfolios.length} PRs`)
}

// ============================================================================
// HELPER: Evolution
// ============================================================================

async function evolve(gen, portfolios) {
  phase(`Evolve ${gen}→${gen + 1}`)
  log(`🧬 Evolving generation ${gen}...`)

  const evolved = await agent(
    `Run evolution to create portfolio for Generation ${gen + 1}.

Portfolios from Gen ${gen}:
${JSON.stringify(portfolios, null, 2)}

Run Python:
cd /Users/wtf403/repos/portfolio-rebalancing
python3 << 'PYEOF'
import json
import sys
sys.path.insert(0, 'experiment')
from evolution import select_best, crossover, mutate, load_asset_universe

portfolios = json.loads('''${JSON.stringify(portfolios)}''')
universe = load_asset_universe()

# Evolution
best = select_best(portfolios, k=2)
print(f"Best fitness: {best[0]['fitness']:.4f}, {best[1]['fitness']:.4f}")

offspring = crossover(best[0], best[1])
evolved = mutate(offspring, universe, 0.15)

evolved['generation'] = ${gen + 1}
evolved['portfolio_id'] = 'gen${gen + 1}_initial'

print(json.dumps(evolved, indent=2))
PYEOF

Parse output and return evolved portfolio JSON.`,
    {
      label: `Evolve ${gen}→${gen + 1}`,
      effort: 'low'
    }
  )

  log(`✅ Evolved portfolio: ${evolved.assets?.length || 0} assets`)

  // Update initial_portfolio.json
  await agent(
    `Write evolved portfolio to experiment/initial_portfolio.json:

${JSON.stringify(evolved, null, 2)}

Then commit and push:
git add experiment/initial_portfolio.json
git commit -m "Gen ${gen + 1}: Evolved from best of Gen ${gen}"
git push origin master`,
    {
      label: 'Update initial',
      effort: 'low'
    }
  )

  return evolved
}

// ============================================================================
// MAIN: RUN 5 GENERATIONS
// ============================================================================

const results = []

for (let gen = 0; gen < 5; gen++) {
  // Deploy generation
  const portfolios = await deployGeneration(gen)

  // Create PRs
  await createPRs(gen, portfolios)

  // Record results
  results.push({
    generation: gen,
    count: portfolios.length,
    portfolios: portfolios.map(p => ({
      agent_id: p.agent_id,
      expected_sharpe: p.expected_sharpe,
      assets_count: p.assets?.length
    }))
  })

  // Evolve (except last generation)
  if (gen < 4) {
    await evolve(gen, portfolios)
  }
}

// ============================================================================
// PHASE: SUMMARY
// ============================================================================

phase('Summary')
log('📊 Generating experiment summary...')

const summary = `
# GA Portfolio Optimization - Experiment Results

## Configuration
- **Generations:** 5
- **Agents per generation:** ${NUM_AGENTS}
- **Total portfolios:** ${results.reduce((s, r) => s + r.count, 0)}
- **Asset universe:** ${universe_csv.split(',').length} tickers

## Results by Generation

${results.map(r => {
  const sharpes = r.portfolios.map(p => p.expected_sharpe || 0)
  const avg = sharpes.reduce((a, b) => a + b, 0) / sharpes.length
  const max = Math.max(...sharpes)
  const min = Math.min(...sharpes)

  return `### Generation ${r.generation}
- **Portfolios:** ${r.count}
- **Avg Sharpe:** ${avg.toFixed(4)}
- **Max Sharpe:** ${max.toFixed(4)}
- **Min Sharpe:** ${min.toFixed(4)}`
}).join('\n\n')}

## Fitness Progression

${results.map(r => {
  const sharpes = r.portfolios.map(p => p.expected_sharpe || 0)
  const avg = sharpes.reduce((a, b) => a + b, 0) / sharpes.length
  return `Gen ${r.generation}: ${avg.toFixed(4)}`
}).join(' → ')}

## All Pull Requests

View at: https://github.com/wtf403/portfolio-rebalancing/pulls

## Success Metrics

✅ ${results.reduce((s, r) => s + r.count, 0)} portfolios generated
✅ ${results.reduce((s, r) => s + r.count, 0)} PRs created
✅ 5 generations completed
✅ Evolution applied between generations

---
*Generated by GA Portfolio Optimization Workflow*
`

log(summary)

// Write summary to file
await agent(
  `Write summary to EXPERIMENT_RESULTS.md:

${summary}

Then git add, commit, push to master`,
  {
    label: 'Save summary'
  }
)

log('✅ Experiment complete!')

return {
  total_portfolios: results.reduce((s, r) => s + r.count, 0),
  generations: 5,
  results: results,
  summary: summary
}
