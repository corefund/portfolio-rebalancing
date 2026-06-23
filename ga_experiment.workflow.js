export const meta = {
  name: 'ga-portfolio-experiment',
  description: 'Run genetic algorithm portfolio optimization across Colab machines',
  phases: [
    { title: 'Setup', detail: 'Extract Colab sessions and prepare configuration' },
    { title: 'Initialize', detail: 'Setup all machines in parallel' },
    { title: 'Generation 0', detail: 'Deploy initial population' },
    { title: 'Generation 1', detail: 'Evolve and deploy' },
    { title: 'Generation 2', detail: 'Evolve and deploy' },
    { title: 'Generation 3', detail: 'Evolve and deploy' },
    { title: 'Generation 4', detail: 'Final generation' },
    { title: 'Summary', detail: 'Analyze results and report best portfolio' }
  ]
};

// Configuration
const NUM_GENERATIONS = 5;
const AGENTS_PER_GENERATION = args?.agents || 20;
const PARALLEL_INIT = 10; // Initialize machines in batches

// Extract SSH commands from colab sessions output
function parseColabSessions(output) {
  const lines = output.split('\n');
  const sessions = [];

  for (const line of lines) {
    if (line.includes('SSH: ssh root@')) {
      const sshCmd = line.split('SSH: ')[1].trim();
      sessions.push(sshCmd);
    }
  }

  return sessions;
}

// Phase 1: Setup - Get Colab sessions
phase('Setup');
log(`Starting GA experiment: ${NUM_GENERATIONS} generations × ${AGENTS_PER_GENERATION} agents`);

const colabOutput = await agent('Get available Colab sessions by running: colab sessions', {
  label: 'Get Colab sessions',
  phase: 'Setup'
});

const sessions = parseColabSessions(colabOutput);
log(`Found ${sessions.length} available Colab sessions`);

if (sessions.length < AGENTS_PER_GENERATION) {
  log(`⚠️ Warning: Only ${sessions.length} sessions available, need ${AGENTS_PER_GENERATION}`);
  log(`Proceeding with ${sessions.length} agents per generation`);
}

const actualAgentsPerGen = Math.min(sessions.length, AGENTS_PER_GENERATION);
const sessionsToUse = sessions.slice(0, actualAgentsPerGen);

// Phase 2: Initialize machines
phase('Initialize');
log(`Initializing ${sessionsToUse.length} machines in parallel (batches of ${PARALLEL_INIT})`);

const initTasks = sessionsToUse.map((sshCmd, idx) => async () => {
  const agentId = `agent_${idx + 1}`;

  return await agent(
    `Initialize Colab machine for ${agentId}:

1. Upload files to machine via scp:
   - init.sh
   - settings.json
   - colab_agent.py

2. SSH to machine: ${sshCmd}

3. Run initialization:
   cd /content && bash init.sh

4. Clone repository:
   git clone https://github.com/corefund/portfolio-rebalancing.git || (cd portfolio-rebalancing && git pull)

5. Verify setup by checking:
   - Python is available
   - Git is configured
   - Repository exists

Return "SUCCESS" if initialization completed, "FAILED" otherwise.`,
    {
      label: `Init ${agentId}`,
      phase: 'Initialize',
      effort: 'low'
    }
  );
});

// Run initialization in batches
const initResults = [];
for (let i = 0; i < initTasks.length; i += PARALLEL_INIT) {
  const batch = initTasks.slice(i, i + PARALLEL_INIT);
  log(`Initializing batch ${Math.floor(i / PARALLEL_INIT) + 1}/${Math.ceil(initTasks.length / PARALLEL_INIT)}...`);
  const batchResults = await parallel(batch);
  initResults.push(...batchResults);
}

const successfulInits = initResults.filter(r => r && r.includes('SUCCESS')).length;
log(`✅ Initialized ${successfulInits}/${sessionsToUse.length} machines`);

if (successfulInits < sessionsToUse.length * 0.8) {
  log(`❌ Less than 80% machines initialized. Aborting experiment.`);
  return { status: 'failed', reason: 'Insufficient machines initialized' };
}

// Generations loop
const allPortfolios = [];

for (let gen = 0; gen < NUM_GENERATIONS; gen++) {
  phase(`Generation ${gen}`);
  log(`\n${'='.repeat(70)}`);
  log(`GENERATION ${gen} - Deploying ${actualAgentsPerGen} agents`);
  log('='.repeat(70));

  // Deploy agents in parallel
  const deployTasks = sessionsToUse.map((sshCmd, idx) => async () => {
    const agentId = `agent_${idx + 1}`;

    return await agent(
      `Deploy portfolio generation agent ${agentId} for Generation ${gen}:

SSH Command: ${sshCmd}

Steps:
1. SSH to machine
2. Navigate to repo: cd /content/portfolio-rebalancing
3. Pull latest: git pull origin master
4. Export environment variables from settings.json:
   export ANTHROPIC_API_KEY="sk-3e442e3188a33a3c-425a71-32bbb64c"
   export ANTHROPIC_BASE_URL="https://router.plus/v1"
   export ANTHROPIC_MODEL="gpt-5.5"
   export AGENT_ID="${agentId}"
   export GENERATION="${gen}"

5. Run agent: python3 colab_agent.py

6. Fetch result: scp from /tmp/portfolio_gen${gen}_${agentId}.json

7. Save locally to: experiment/results/gen${gen}_${agentId}_portfolio.json

Return the portfolio JSON content if successful, or "FAILED: reason" if failed.`,
      {
        label: `Deploy gen${gen} ${agentId}`,
        phase: `Generation ${gen}`,
        effort: 'low'
      }
    );
  });

  log(`Deploying ${deployTasks.length} agents in parallel...`);
  const deployResults = await parallel(deployTasks);

  const successfulDeploys = deployResults.filter(r => r && !r.includes('FAILED')).length;
  log(`✅ ${successfulDeploys}/${deployTasks.length} agents completed`);

  if (successfulDeploys < deployTasks.length * 0.8) {
    log(`⚠️ Less than 80% success rate in generation ${gen}`);
  }

  // Collect portfolios from this generation
  log(`\nCollecting portfolios from generation ${gen}...`);

  const portfolios = await agent(
    `Read all portfolio files from experiment/results/gen${gen}_*_portfolio.json and return their fitness scores.

Calculate fitness for each using the fitness function from experiment/evolution.py.
Return a summary showing:
- Agent ID
- Fitness score
- Top 3 assets by weight

Format as a table.`,
    {
      label: `Collect gen${gen} results`,
      phase: `Generation ${gen}`
    }
  );

  allPortfolios.push({ generation: gen, summary: portfolios });

  // Evolution (if not last generation)
  if (gen < NUM_GENERATIONS - 1) {
    log(`\n🧬 Running evolution for generation ${gen}...`);

    const evolutionResult = await agent(
      `Run evolution to create initial portfolio for generation ${gen + 1}:

1. Load all portfolios from experiment/results/gen${gen}_*_portfolio.json

2. Use evolution.py functions:
   - calculate_fitness() for each portfolio
   - select_best(portfolios, k=2) to get top 2
   - crossover(parent1, parent2) to blend
   - mutate(offspring, universe) for variation

3. Save evolved portfolio to experiment/initial_portfolio.json with:
   - generation: ${gen + 1}
   - portfolio_id: "gen${gen + 1}_initial"
   - assets: [evolved assets]
   - parent: "best_agent_id"
   - parent_fitness: best_fitness

4. Commit and push to master:
   git add experiment/initial_portfolio.json
   git commit -m "feat: Evolution gen${gen} → gen${gen + 1}"
   git push origin master

Return the evolved portfolio summary and parent fitness scores.`,
      {
        label: `Evolution gen${gen}→${gen + 1}`,
        phase: `Generation ${gen}`
      }
    );

    log(`✅ Evolution complete: ${evolutionResult}`);
  }
}

// Phase 8: Summary
phase('Summary');
log(`\n${'='.repeat(70)}`);
log('EXPERIMENT COMPLETE - ANALYZING RESULTS');
log('='.repeat(70));

const finalSummary = await agent(
  `Generate comprehensive experiment summary:

1. Load all portfolios from all generations (experiment/results/*.json)

2. Calculate statistics:
   - Best fitness per generation
   - Average fitness per generation
   - Fitness improvement over generations
   - Best overall portfolio

3. Identify best portfolio with:
   - Agent ID and generation
   - Fitness score
   - All metrics (Sharpe, Sortino, CAGR, etc.)
   - Full asset allocation

4. Create summary report showing:
   - Generation-by-generation progress
   - Top 5 portfolios overall
   - Key insights and patterns

Return detailed markdown report.`,
  {
    label: 'Generate final report',
    phase: 'Summary'
  }
);

log('\n' + finalSummary);

return {
  status: 'success',
  generations: NUM_GENERATIONS,
  agents_per_generation: actualAgentsPerGen,
  total_portfolios: NUM_GENERATIONS * actualAgentsPerGen,
  summary: finalSummary
};
