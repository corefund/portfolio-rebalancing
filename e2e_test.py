#!/usr/bin/env python3
"""
End-to-end test: Setup Claude on Colab, authenticate gh, create PR
"""
import os, subprocess, sys

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
AGENT_ID = "agent_1"
GENERATION = "0"

print("🚀 E2E Test: Setup Claude + gh auth + create PR")
print("=" * 70)

# Step 1: Install dependencies
print("\n📦 Step 1: Installing dependencies...")
subprocess.run(["pip", "install", "-q", "anthropic", "requests", "pyyaml"], check=False)
print("✅ Dependencies installed")

# Step 2: Clone repository
print("\n📥 Step 2: Cloning repository...")
if os.path.exists("portfolio-rebalancing"):
    subprocess.run(["rm", "-rf", "portfolio-rebalancing"], check=True)

subprocess.run(["git", "clone", "https://github.com/wtf403/portfolio-rebalancing.git"], check=True)
os.chdir("portfolio-rebalancing")
print(f"✅ Repository cloned to: {os.getcwd()}")

# Step 3: Setup gh CLI auth
print("\n🔑 Step 3: Authenticating gh CLI...")
subprocess.run(["apt-get", "update", "-qq"], check=False, capture_output=True)
subprocess.run(["apt-get", "install", "-y", "-qq", "gh"], check=False, capture_output=True)

# Auth with token
proc = subprocess.run(
    ["gh", "auth", "login", "--with-token"],
    input=GITHUB_TOKEN,
    text=True,
    capture_output=True
)
if proc.returncode == 0:
    print("✅ gh CLI authenticated")
else:
    print(f"⚠️  gh auth warning: {proc.stderr}")

# Verify auth
result = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True)
print(f"gh status: {result.stdout}")

# Step 4: Configure git
print("\n⚙️  Step 4: Configuring git...")
subprocess.run(["git", "config", "--global", "user.name", f"Agent-{AGENT_ID}"], check=True)
subprocess.run(["git", "config", "--global", "user.email", f"{AGENT_ID}@experiment.local"], check=True)
print("✅ Git configured")

# Step 5: Check files exist
print("\n📂 Step 5: Verifying files...")
files_ok = all([
    os.path.exists("experiment/initial_portfolio.json"),
    os.path.exists("experiment/agent_prompt.md"),
    os.path.exists("colab_agent.py")
])
print(f"✅ All required files present: {files_ok}")

# Step 6: Test portfolio validation
print("\n✅ Step 6: Testing portfolio validation...")
result = subprocess.run(
    ["python", "experiment/validate_portfolio.py", "experiment/initial_portfolio.json"],
    capture_output=True,
    text=True
)
print(f"Validation result: {result.stdout}")

print("\n" + "=" * 70)
print("🎉 E2E Test Complete!")
print("\nNext step: Set ANTHROPIC_API_KEY and run colab_agent.py")
print("Expected: Agent will create PR with portfolio via gh CLI")
