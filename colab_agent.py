#!/usr/bin/env python3
"""
Portfolio Rebalancing Agent - runs on Google Colab
Receives a portfolio, rebalances it using Claude, creates MR
"""

import os
import json
import requests
import subprocess
from datetime import datetime
from pathlib import Path

# Environment variables (set in Colab secrets)
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
AGENT_ID = os.environ.get("AGENT_ID", "agent_1")
GENERATION = int(os.environ.get("GENERATION", "0"))

REPO_URL = "https://github.com/wtf403/portfolio-rebalancing.git"
UNIVERSE_URL = "https://docs.google.com/spreadsheets/d/1f3xJomL2UlCn7887jpX_MQZBsQWbmVKiQXsUdZ3kkcE/export?format=csv"


def setup_git():
    """Configure git with credentials"""
    subprocess.run(["git", "config", "--global", "user.name", f"Agent-{AGENT_ID}"])
    subprocess.run(["git", "config", "--global", "user.email", f"{AGENT_ID}@experiment.local"])


def clone_repo():
    """Clone repository"""
    repo_dir = Path("repo")

    if repo_dir.exists():
        print("📂 Removing old repo...")
        subprocess.run(["rm", "-rf", "repo"], check=True)

    print(f"📥 Cloning repository...")
    result = subprocess.run([
        "git", "clone",
        f"https://{GITHUB_TOKEN}@github.com/wtf403/portfolio-rebalancing.git",
        "repo"
    ], check=True, capture_output=True, text=True)

    print(f"📂 Changing to repo directory...")
    os.chdir("repo")
    print(f"✅ Current dir: {os.getcwd()}")


def load_current_portfolio():
    """Load current portfolio from experiment/initial_portfolio.json"""
    with open("experiment/initial_portfolio.json") as f:
        return json.load(f)


def load_universe():
    """Download asset universe CSV"""
    response = requests.get(UNIVERSE_URL)
    response.raise_for_status()

    with open("universe.csv", "w") as f:
        f.write(response.text)

    return response.text[:1000]  # Return preview


def load_agent_prompt():
    """Load agent prompt template"""
    with open("experiment/agent_prompt.md") as f:
        return f.read()


def call_claude_api(prompt: str) -> str:
    """Call Claude API to rebalance portfolio"""
    url = "https://api.anthropic.com/v1/messages"

    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }

    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 4000,
        "temperature": 0.7,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()

    result = response.json()
    return result["content"][0]["text"]


def extract_json_from_response(response: str) -> dict:
    """Extract JSON object from Claude's response"""
    # Try to find JSON block
    start = response.find("{")
    end = response.rfind("}") + 1

    if start == -1 or end == 0:
        raise ValueError("No JSON found in response")

    json_str = response[start:end]
    return json.loads(json_str)


def validate_portfolio(portfolio: dict) -> bool:
    """Validate portfolio constraints"""
    total_weight = sum(asset["weight"] for asset in portfolio["assets"])

    # Check total weight
    if abs(total_weight - 1.0) > 0.01:
        print(f"❌ Total weight {total_weight} != 1.0")
        return False

    # Check individual weights
    for asset in portfolio["assets"]:
        weight = asset["weight"]
        if weight < 0.05 or weight > 0.25:
            print(f"❌ Asset {asset['ticker']} weight {weight} out of bounds [0.05, 0.25]")
            return False

    # Check number of assets
    if len(portfolio["assets"]) < 8 or len(portfolio["assets"]) > 12:
        print(f"❌ Number of assets {len(portfolio['assets'])} out of bounds [8, 12]")
        return False

    print("✅ Portfolio validation passed")
    return True


def create_branch_and_commit(portfolio: dict):
    """Create new branch with proposed portfolio"""
    branch_name = f"{AGENT_ID}_gen{GENERATION}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    subprocess.run(["git", "checkout", "-b", branch_name], check=True)

    # Save proposed portfolio
    output_file = f"experiment/results/gen{GENERATION}_{AGENT_ID}_portfolio.json"
    os.makedirs("experiment/results", exist_ok=True)

    with open(output_file, "w") as f:
        json.dump(portfolio, f, indent=2)

    subprocess.run(["git", "add", output_file], check=True)

    commit_msg = f"[Gen {GENERATION}] Portfolio proposal by {AGENT_ID}\n\nExpected Sharpe: {portfolio.get('expected_sharpe', 'N/A')}"
    subprocess.run(["git", "commit", "-m", commit_msg], check=True)

    subprocess.run(["git", "push", "origin", branch_name], check=True)

    return branch_name


def create_pull_request(branch_name: str, portfolio: dict):
    """Create GitHub Pull Request"""
    url = "https://api.github.com/repos/wtf403/portfolio-rebalancing/pulls"

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    title = f"[Gen {GENERATION}] Portfolio by {AGENT_ID}"
    body = f"""## Portfolio Rebalancing Proposal

**Agent:** {AGENT_ID}
**Generation:** {GENERATION}
**Expected Sharpe:** {portfolio.get('expected_sharpe', 'N/A')}

### Assets
"""

    for asset in portfolio["assets"]:
        body += f"- **{asset['ticker']}**: {asset['weight']:.2%}"
        if 'reason' in asset:
            body += f" - {asset['reason']}"
        body += "\n"

    body += f"\n### Explanation\n{portfolio.get('explanation', 'No explanation provided')}"

    payload = {
        "title": title,
        "body": body,
        "head": branch_name,
        "base": "master"
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()

    pr_data = response.json()
    print(f"✅ Pull Request created: {pr_data['html_url']}")

    return pr_data


def main():
    print(f"🚀 Starting agent {AGENT_ID} for generation {GENERATION}")

    # Setup
    setup_git()
    clone_repo()

    # Load inputs
    print("📂 Loading portfolio and universe...")
    current_portfolio = load_current_portfolio()
    universe_preview = load_universe()
    agent_prompt_template = load_agent_prompt()

    # Build prompt for Claude
    prompt = f"""{agent_prompt_template}

## Current Portfolio (Generation {GENERATION})

```json
{json.dumps(current_portfolio, indent=2)}
```

## Asset Universe (Preview)

```
{universe_preview}
...
(Full universe available in universe.csv)
```

## Your Agent ID

{AGENT_ID}

---

Now propose your rebalanced portfolio as JSON:
"""

    print("🤖 Calling Claude API...")
    response = call_claude_api(prompt)

    print("📝 Claude's response:")
    print(response[:500] + "..." if len(response) > 500 else response)

    # Parse response
    print("🔍 Extracting portfolio JSON...")
    proposed_portfolio = extract_json_from_response(response)

    # Validate
    print("✅ Validating portfolio...")
    if not validate_portfolio(proposed_portfolio):
        print("❌ Portfolio validation failed. Exiting.")
        return 1

    # Create MR
    print("📤 Creating branch and pull request...")
    branch_name = create_branch_and_commit(proposed_portfolio)
    pr_data = create_pull_request(branch_name, proposed_portfolio)

    print(f"✅ Success! PR #{pr_data['number']} created")

    return 0


if __name__ == "__main__":
    exit(main())
