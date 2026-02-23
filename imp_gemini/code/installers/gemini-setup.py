#!/usr/bin/env python3
"""
AI SDLC Method v2 - Project Setup (Gemini CLI)

Self-contained installer for Gemini CLI users.

# Implements: REQ-TOOL-011 (Installability), REQ-TOOL-007 (Project Scaffolding)
"""

import sys
import json
import argparse
import shutil
import urllib.request
import urllib.error
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Tuple

# =============================================================================
# Configuration
# =============================================================================

GITHUB_REPO = "foolishimp/ai_sdlc_method"
SKILL_NAME = "genesis-bootloader"
PLUGIN_BASE = f"imp_gemini/code/skills/{SKILL_NAME}"
GITHUB_RAW = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main"

GRAPH_TOPOLOGY_URL = f"{GITHUB_RAW}/imp_gemini/code/config/graph_topology.yml"
BOOTLOADER_URL = f"{GITHUB_RAW}/specification/GENESIS_BOOTLOADER.md"
SKILL_MD_URL = f"{GITHUB_RAW}/{PLUGIN_BASE}/SKILL.md"

VERSION = "2.8.0"

# =============================================================================
# Templates
# =============================================================================

PROJECT_CONSTRAINTS_TEMPLATE = """
# Project Constraints — {project_name}
# Implements: REQ-CTX-001 (Context as Constraint Surface)

project:
  name: "{project_name}"
  kind: ""
  language: ""
  test_runner: ""

constraints:
  ecosystem_compatibility:
    language: ""
    version: ""
  deployment_target:
    platform: ""
  security_model:
    authentication: ""
  build_system:
    tool: ""

structure:
  design_tenants: []
  root_code_policy: reject
"""

INTENT_TEMPLATE = """
# {project_name} — Intent

**Intent ID**: INT-001
**Date**: {date}
**Priority**: High
**Status**: Draft

---

## The Problem
<!-- What problem does this project solve? -->

---

## What We Want
<!-- Describe the desired outcome in business language. -->
"""

# =============================================================================
# Helpers
# =============================================================================

def print_banner(title: str):
    print("\n" + "="*60)
    print(f"  AI SDLC Method v2 (Gemini) - {title}")
    print("="*60 + "\n")

def print_ok(msg: str): print(f"  [OK] {msg}")
def print_error(msg: str): print(f"  [ERROR] {msg}")
def print_warn(msg: str): print(f"  [WARN] {msg}")

def fetch_url(url: str) -> str:
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            return response.read().decode("utf-8")
    except Exception:
        return ""

def detect_project_name(target: Path) -> str:
    return target.name

# =============================================================================
# Logic
# =============================================================================

def setup_workspace(target: Path, project_name: str, dry_run: bool):
    print("--- Workspace Setup ---")
    ws = target / ".ai-workspace"
    dirs = [
        ws / "events",
        ws / "features" / "active",
        ws / "features" / "completed",
        ws / "graph",
        ws / "context",
        ws / "spec",
        ws / "tasks" / "active",
    ]
    
    if not dry_run:
        for d in dirs: d.mkdir(parents=True, exist_ok=True)
        
        # Files
        (ws / "events" / "events.jsonl").touch()
        
        constraints_path = ws / "context" / "project_constraints.yml"
        if not constraints_path.exists():
            constraints_path.write_text(PROJECT_CONSTRAINTS_TEMPLATE.format(project_name=project_name))
            print_ok("Created project_constraints.yml")
            
        # Topology
        topology_path = ws / "graph" / "graph_topology.yml"
        if not topology_path.exists():
            content = fetch_url(GRAPH_TOPOLOGY_URL)
            if content:
                topology_path.write_text(content)
                print_ok("Fetched graph_topology.yml")
                
        # Intent
        spec_dir = target / "specification"
        spec_dir.mkdir(exist_ok=True)
        intent_path = spec_dir / "INTENT.md"
        if not intent_path.exists():
            intent_path.write_text(INTENT_TEMPLATE.format(project_name=project_name, date=datetime.now().strftime("%Y-%m-%d")))
            print_ok("Created specification/INTENT.md")
            
        # Initial Event
        event = {
            "event_type": "project_initialized",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "project": project_name,
            "data": {"method_version": VERSION, "installer": "gemini-setup.py"}
        }
        with open(ws / "events" / "events.jsonl", "a") as f:
            f.write(json.dumps(event) + "\n")
    else:
        print("  [DRY RUN] Would create .ai-workspace and initial files")

def install_skill(dry_run: bool):
    print("--- Skill Installation ---")
    if dry_run:
        print("  [DRY RUN] Would install genesis-bootloader skill")
        return

    # Create temporary skill directory
    tmp_dir = Path(".gemini_tmp_skill")
    tmp_dir.mkdir(exist_ok=True)
    (tmp_dir / "references").mkdir(exist_ok=True)
    
    try:
        skill_md = fetch_url(SKILL_MD_URL)
        bootloader_md = fetch_url(BOOTLOADER_URL)
        
        if not skill_md or not bootloader_md:
            print_error("Could not fetch skill files from GitHub")
            return

        (tmp_dir / "SKILL.md").write_text(skill_md)
        (tmp_dir / "references" / "GENESIS_BOOTLOADER.md").write_text(bootloader_md)
        
        # Install via gemini CLI
        print("  Running: gemini skills install .gemini_tmp_skill --scope workspace")
        subprocess.run(["gemini", "skills", "install", str(tmp_dir), "--scope", "workspace"], check=True)
        print_ok("Skill 'genesis-bootloader' installed to workspace")
        
    except Exception as e:
        print_error(f"Failed to install skill: {e}")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

def main():
    parser = argparse.ArgumentParser(description="AI SDLC Project Setup for Gemini")
    parser.add_argument("--target", default=".", help="Target directory")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes")
    parser.add_argument("--skip-skill", action="store_true", help="Skip skill installation")
    args = parser.parse_args()

    target = Path(args.target).resolve()
    project_name = detect_project_name(target)
    
    print_banner("Project Setup")
    setup_workspace(target, project_name, args.dry_run)
    if not args.skip_skill:
        install_skill(args.dry_run)
    
    print("\nSetup Complete!")
    print("Next steps:")
    print("  1. In Gemini CLI, run: /skills reload")
    print("  2. Run: /gen-start to begin\n")

if __name__ == "__main__":
    main()
