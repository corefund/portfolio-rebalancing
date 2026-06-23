#!/usr/bin/env python3
"""
Program.py - Main orchestrator for GA portfolio optimization experiment

This script coordinates the genetic algorithm experiment across multiple
Colab machines using Claude Code workflow orchestration.

Usage:
    python3 program.py --generations 5 --agents 20
"""

import argparse
import json
import subprocess
from pathlib import Path
from typing import List, Dict


def load_config():
    """Load configuration from settings.json"""
    with open('settings.json') as f:
        settings = json.load(f)
    return settings


def get_colab_sessions(count: int) -> List[str]:
    """Get list of available Colab SSH sessions"""
    result = subprocess.run(
        ['colab', 'sessions'],
        capture_output=True,
        text=True
    )

    lines = result.stdout.split('\n')
    ssh_lines = [line for line in lines if 'SSH:' in line]
    sessions = []

    for line in ssh_lines:
        ssh_cmd = line.split('SSH:')[1].strip()
        sessions.append(ssh_cmd)

    return sessions[:count]


def init_machine(ssh_cmd: str, settings: dict) -> bool:
    """Initialize a Colab machine with init.sh"""
    print(f"🔧 Initializing machine: {ssh_cmd}")

    # Extract host and port
    parts = ssh_cmd.split()
    host_port = ' '.join(parts[1:])

    # Copy files to machine
    try:
        # Copy init.sh and settings.json
        subprocess.run(
            f"scp -o StrictHostKeyChecking=no init.sh settings.json {host_port}:/content/",
            shell=True,
            check=True,
            capture_output=True
        )

        # Run init.sh
        subprocess.run(
            f"{ssh_cmd} 'cd /content && bash init.sh'",
            shell=True,
            check=True,
            capture_output=True,
            timeout=300
        )

        print(f"✅ Machine initialized: {ssh_cmd}")
        return True

    except Exception as e:
        print(f"❌ Failed to initialize {ssh_cmd}: {e}")
        return False


def run_experiment(generations: int, agents_per_gen: int):
    """Run the full GA experiment"""
    print("╔══════════════════════════════════════════════════════════════════════════╗")
    print("║                                                                          ║")
    print("║         🧬 GA PORTFOLIO OPTIMIZATION EXPERIMENT                          ║")
    print("║                                                                          ║")
    print("╚══════════════════════════════════════════════════════════════════════════╝")
    print()
    print(f"Configuration:")
    print(f"  Generations: {generations}")
    print(f"  Agents per generation: {agents_per_gen}")
    print(f"  Total portfolios: {generations * agents_per_gen}")
    print()

    # Load settings
    settings = load_config()

    # Get Colab sessions
    print(f"📡 Getting {agents_per_gen} Colab sessions...")
    sessions = get_colab_sessions(agents_per_gen)
    print(f"✅ Found {len(sessions)} sessions")

    if len(sessions) < agents_per_gen:
        print(f"⚠️  Only {len(sessions)} sessions available, using those")
        agents_per_gen = len(sessions)

    # Initialize all machines in parallel
    print()
    print("🔧 Initializing machines...")
    # TODO: This should be done via Claude workflow for parallelization

    # Run generations via Claude workflow
    print()
    print("🚀 Starting experiment workflow...")
    print("📝 See program.md for workflow specification")
    print()
    print("⚠️  This should be executed via Claude Code workflow, not directly")
    print("    Use: claude workflow program.md")


def main():
    parser = argparse.ArgumentParser(
        description='Run GA portfolio optimization experiment'
    )
    parser.add_argument(
        '--generations',
        type=int,
        default=5,
        help='Number of generations to run (default: 5)'
    )
    parser.add_argument(
        '--agents',
        type=int,
        default=20,
        help='Number of agents per generation (default: 20)'
    )

    args = parser.parse_args()

    run_experiment(args.generations, args.agents)


if __name__ == '__main__':
    main()
