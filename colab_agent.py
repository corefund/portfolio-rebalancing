#!/usr/bin/env python3
"""
Portfolio Optimization Agent for Colab
Generates portfolio using Claude API based on initial portfolio and constraints
"""

import os
import sys
import json
from pathlib import Path
from anthropic import Anthropic

# Get environment variables
AGENT_ID = os.environ.get('AGENT_ID', 'agent_1')
GENERATION = int(os.environ.get('GENERATION', '0'))
API_KEY = os.environ.get('ANTHROPIC_API_KEY')
BASE_URL = os.environ.get('ANTHROPIC_BASE_URL', 'https://api.anthropic.com')
MODEL = os.environ.get('ANTHROPIC_MODEL', 'claude-sonnet-4-20250514')

def load_initial_portfolio():
    """Load initial portfolio for this generation"""
    portfolio_path = Path('experiment/initial_portfolio.json')
    if portfolio_path.exists():
        with open(portfolio_path) as f:
            return json.load(f)
    return None

def load_agent_prompt():
    """Load agent prompt template"""
    prompt_path = Path('experiment/agent_prompt.md')
    if prompt_path.exists():
        with open(prompt_path) as f:
            return f.read()
    return ""

def load_asset_universe():
    """Load asset universe from CSV URL"""
    import pandas as pd
    csv_url = "https://docs.google.com/spreadsheets/d/1f3xJomL2UlCn7887jpX_MQZBsQWbmVKiQXsUdZ3kkcE/export?format=csv"

    try:
        df = pd.read_csv(csv_url)
        tickers = [col for col in df.columns if col != 'Date']
        return tickers
    except Exception as e:
        print(f"Failed to load asset universe: {e}")
        # Fallback to common tickers
        return ["SPY", "QQQ", "AGG", "GLD", "VNQ", "AAPL", "MSFT", "GOOGL", "NVDA", "BTC-USD"]

def generate_portfolio():
    """Generate portfolio using Claude API"""

    print(f"🤖 Agent {AGENT_ID} - Generation {GENERATION}")
    print("="*60)

    # Load data
    initial_portfolio = load_initial_portfolio()
    agent_prompt = load_agent_prompt()
    universe = load_asset_universe()

    print(f"📊 Asset universe: {len(universe)} tickers")

    if initial_portfolio:
        print(f"📂 Initial portfolio loaded: {len(initial_portfolio['assets'])} assets")

    # Build prompt
    system_prompt = agent_prompt if agent_prompt else """You are a portfolio optimization agent.
Create a diversified portfolio that maximizes risk-adjusted returns."""

    user_message = f"""Generate an optimized portfolio for Generation {GENERATION}.

Asset Universe: {', '.join(universe[:50])}... (total {len(universe)} assets available)

Constraints:
- Total weight must equal 1.0
- Minimum weight per asset: 0.05 (5%)
- Maximum weight per asset: 0.25 (25%)
- Number of assets: 8-12
- Use tickers from the asset universe only

"""

    if initial_portfolio:
        user_message += f"""
Starting Portfolio (Generation {initial_portfolio.get('generation', 0)}):
{json.dumps(initial_portfolio['assets'], indent=2)}

Improve this portfolio by:
1. Adjusting weights to optimize the fitness function
2. Replacing underperforming assets
3. Maintaining diversification

"""

    user_message += """
Output ONLY a valid JSON object (no markdown, no explanations):
{
  "generation": """ + str(GENERATION) + """,
  "portfolio_id": "gen""" + str(GENERATION) + """_""" + AGENT_ID + """",
  "agent_name": \"""" + AGENT_ID + """\",
  "assets": [
    {"ticker": "TICKER", "weight": 0.XX, "reason": "brief reason"}
  ],
  "explanation": "Brief explanation of your strategy"
}
"""

    # Call Claude API
    print("\n🔄 Calling Claude API...")

    try:
        client = Anthropic(api_key=API_KEY, base_url=BASE_URL)

        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )

        result_text = response.content[0].text

        # Try to extract JSON if wrapped in markdown
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()

        portfolio = json.loads(result_text)

        # Validate
        total_weight = sum(asset['weight'] for asset in portfolio['assets'])
        num_assets = len(portfolio['assets'])

        print(f"\n✅ Portfolio generated:")
        print(f"   Assets: {num_assets}")
        print(f"   Total weight: {total_weight:.4f}")

        # Save to file
        output_path = f"/tmp/portfolio_gen{GENERATION}_{AGENT_ID}.json"
        with open(output_path, 'w') as f:
            json.dump(portfolio, f, indent=2)

        print(f"   Saved to: {output_path}")

        return portfolio

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    if not API_KEY:
        print("❌ ANTHROPIC_API_KEY environment variable not set")
        sys.exit(1)

    portfolio = generate_portfolio()
    print("\n" + "="*60)
    print("✅ Agent completed successfully")
