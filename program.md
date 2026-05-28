# GA Portfolio Research Program

This is an experiment to have the LLM do its own portfolio research.

## Setup

To set up a new experiment, work with the user to:

1. **Agree on a run tag**: propose a tag based on today's date (e.g. `may28`). The branch `autoresearch/<tag>` must not already exist — this is a fresh run.
2. **Create the branch**: `git checkout -b autoresearch/<tag>` from current main.
3. **Read the in-scope files**: The repo is small. Read these files for full context:
   - `README.md` — repository context.
   - `prepare.py` — fixed constants, benchmark config, data loading, evaluation. **Do not modify.**
   - `strategy.py` — the file you modify. Chromosome encoding, GA operators, rebalance logic.
4. **Initialize results.tsv**: Create `results.tsv` with just the header row. The baseline will be recorded after the first run.
5. **Confirm and go**: Confirm setup looks good.

Once you get confirmation, kick off the experimentation.

## Experimentation

Each experiment runs a backtest on the **validation split** (2019-2021). You launch it simply as: `python strategy.py`.

**What you CAN do:**
- Modify `strategy.py` — this is the only file you edit. Everything is fair game: chromosome encoding, mutation operators, crossover logic, rebalance triggers, top_k selection, etc.

**What you CANNOT do:**
- Modify `prepare.py`. It is read-only. It contains the fixed evaluation, benchmark config, and fitness function.
- Install new packages or add dependencies. You can only use what's already in `requirements.txt`.
- Modify the fitness function. The `evaluate_portfolio` function in `prepare.py` is the ground truth metric.

**The goal is simple: get the highest composite_score.** The fitness function is locked, so you can only improve by making the GA strategy smarter.

**Simplicity criterion**: All else being equal, simpler is better. A small improvement that adds ugly complexity is not worth it. Conversely, removing something and getting equal or better results is a great outcome — that's a simplification win.

**The first run**: Your very first run should always be to establish the baseline, so you will run the strategy script as is.

## Output format

Once the script finishes it prints a summary like this:

```
---
composite_score:  1.184000
sharpe:           1.2000
cagr:             0.0800
max_drawdown:     -0.1500
turnover:         0.3000
volatility:       0.1200
```

You can extract the key metric from the log file:

```
grep "^composite_score:" run.log
```

## Logging results

When an experiment is done, log it to `results.tsv` (tab-separated, NOT comma-separated).

The TSV has a header row and 4 columns:

```
commit	composite_score	status	description
```

1. git commit hash (short, 7 chars)
2. composite_score achieved (e.g. 1.234567) — use 0.000000 for crashes
3. status: `keep`, `discard`, or `crash`
4. short text description of what this experiment tried

Example:

```
commit	composite_score	status	description
a1b2c3d	1.184000	keep	baseline
b2c3d4e	1.236000	keep	increase mutation rate to 0.15
c3d4e5f	1.150000	discard	switch to equal-weight allocation
d4e5f6g	0.000000	crash	negative top_k (bug)
```

## The experiment loop

The experiment runs on a dedicated branch (e.g. `autoresearch/may28`).

LOOP FOREVER:

1. Look at the git state: the current branch/commit we're on
2. Tune `strategy.py` with an experimental idea by directly hacking the code.
3. git commit
4. Run the experiment: `python strategy.py > run.log 2>&1` (redirect everything — do NOT use tee or let output flood your context)
5. Read out the results: `grep "^composite_score:" run.log`
6. If the grep output is empty, the run crashed. Run `tail -n 50 run.log` to read the Python stack trace and attempt a fix. If you can't get things to work after more than a few attempts, give up.
7. Record the results in the tsv (NOTE: do not commit the results.tsv file, leave it untracked by git)
8. If composite_score improved (higher), you "advance" the branch, keeping the git commit
9. If composite_score is equal or worse, you git reset back to where you started

The idea is that you are a completely autonomous researcher trying things out. If they work, keep. If they don't, discard. And you're advancing the branch so that you can iterate.

**Crashes**: If a run crashes (data fetch error, or a bug, or etc.), use your judgment: If it's something dumb and easy to fix (e.g. a typo, a missing import), fix it and re-run. If the idea itself is fundamentally broken, just skip it, log "crash" as the status in the tsv, and move on.

**NEVER STOP**: Once the experiment loop has begun (after the initial setup), do NOT pause to ask the human if you should continue. Do NOT ask "should I keep going?" or "is this a good stopping point?". The human might be asleep, or gone from a computer and expects you to continue working *indefinitely* until you are manually stopped. You are autonomous. If you run out of ideas, think harder — try combining previous near-misses, try more radical changes to the GA operators, try different rebalance triggers. The loop runs until the human interrupts you, period.
