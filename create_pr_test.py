#!/usr/bin/env python3
"""
Create a real PR with mock portfolio (testing gh CLI integration)
"""
import os, subprocess, sys, json

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
AGENT_ID = "agent_test"
GENERATION = 0

print("🚀 Creating test PR with mock portfolio")
print("=" * 70)

# Setup
print("\n📦 Installing dependencies...")
subprocess.run(["pip", "install", "-q", "requests"], check=False)
subprocess.run(["apt-get", "update", "-qq"], check=False, capture_output=True)
subprocess.run(["apt-get", "install", "-y", "-qq", "gh"], check=False, capture_output=True)

print("\n📥 Cloning repository...")
if os.path.exists("portfolio-rebalancing"):
    subprocess.run(["rm", "-rf", "portfolio-rebalancing"], check=True)

subprocess.run([
    "git", "clone",
    f"https://{GITHUB_TOKEN}@github.com/wtf403/portfolio-rebalancing.git"
], check=True)
os.chdir("portfolio-rebalancing")

# Configure git
print("\n⚙️  Configuring git...")
subprocess.run(["git", "config", "user.name", "Test-Agent"], check=True)
subprocess.run(["git", "config", "user.email", "test@experiment.local"], check=True)

# Auth gh
proc = subprocess.run(
    ["gh", "auth", "login", "--with-token"],
    input=GITHUB_TOKEN,
    text=True,
    capture_output=True
)
print(f"✅ gh authenticated: {proc.returncode == 0}")

# Create branch
branch_name = f"gen{GENERATION}_{AGENT_ID}_test"
print(f"\n🌿 Creating branch: {branch_name}")
subprocess.run(["git", "checkout", "-b", branch_name], check=True)

# Create mock portfolio
portfolio = {
    "generation": GENERATION,
    "agent_id": AGENT_ID,
    "timestamp": "2024-06-21T12:00:00Z",
    "expected_sharpe": 1.45,
    "explanation": "Test portfolio created by E2E test. Diversified across tech, bonds, and gold.",
    "assets": [
        {"ticker": "QQQ", "weight": 0.25, "reason": "Tech exposure"},
        {"ticker": "SPY", "weight": 0.20, "reason": "Broad market"},
        {"ticker": "AGG", "weight": 0.20, "reason": "Bond allocation"},
        {"ticker": "GLD", "weight": 0.15, "reason": "Gold hedge"},
        {"ticker": "VTI", "weight": 0.20, "reason": "Total market"}
    ]
}

output_file = f"experiment/results/gen{GENERATION}_{AGENT_ID}_portfolio.json"
print(f"\n📝 Creating portfolio: {output_file}")
with open(output_file, "w") as f:
    json.dump(portfolio, f, indent=2)

# Commit
subprocess.run(["git", "add", output_file], check=True)
commit_msg = f"[Gen {GENERATION}] Test portfolio by {AGENT_ID}\n\nExpected Sharpe: {portfolio['expected_sharpe']}"
subprocess.run(["git", "commit", "-m", commit_msg], check=True)
print("✅ Committed")

# Push
print(f"\n⬆️  Pushing to origin/{branch_name}...")
result = subprocess.run(
    ["git", "push", "-u", "origin", branch_name],
    capture_output=True,
    text=True
)
if result.returncode == 0:
    print("✅ Pushed successfully")
else:
    print(f"❌ Push failed: {result.stderr}")
    sys.exit(1)

# Create PR using gh CLI
print("\n📨 Creating Pull Request...")
title = f"[Gen {GENERATION}] Test Portfolio by {AGENT_ID}"
body = f"""## Test Portfolio Rebalancing

**Agent:** {AGENT_ID}
**Generation:** {GENERATION}
**Expected Sharpe:** {portfolio['expected_sharpe']}

### Assets
"""
for asset in portfolio["assets"]:
    body += f"- **{asset['ticker']}**: {asset['weight']:.2%} - {asset['reason']}\n"

body += f"\n### Explanation\n{portfolio['explanation']}"

# Create PR with gh CLI
result = subprocess.run(
    ["gh", "pr", "create", 
     "--title", title,
     "--body", body,
     "--base", "master",
     "--head", branch_name],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    pr_url = result.stdout.strip()
    print(f"✅ PR created: {pr_url}")
else:
    print(f"⚠️  gh pr create output: {result.stderr}")
    # Fallback: try via API
    print("\n🔄 Trying via GitHub API...")
    import requests
    url = "https://api.github.com/repos/wtf403/portfolio-rebalancing/pulls"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    payload = {
        "title": title,
        "body": body,
        "head": branch_name,
        "base": "master"
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 201:
        pr_data = response.json()
        print(f"✅ PR created via API: {pr_data['html_url']}")
    else:
        print(f"❌ API error: {response.status_code} - {response.text}")

print("\n" + "=" * 70)
print("🎉 E2E Test Complete - PR Created!")
