#!/usr/bin/env python3
# Implements: REQ-TOOL-011 (Installability), REQ-TOOL-003 (Workflow Commands), REQ-TOOL-007 (Project Scaffolding)
# Implements: REQ-TOOL-012 (Multi-Tenant Folder Structure), REQ-TOOL-014 (Observability Integration Contract)
# Implements: REQ-TOOL-001 (Plugin Architecture — installable .claude-plugin bundle, versioned, discoverable)
# Implements: REQ-TOOL-015 (Workspace Placement at Project Root — AC-2 warning when run inside imp_* tenant)
"""
AI SDLC Method v2 - Project Setup

Self-contained installer that can be run directly from GitHub.

Usage:
    # Install from GitHub public repo (one-liner)
    curl -sL https://raw.githubusercontent.com/foolishimp/ai_sdlc_method/main/imp_claude/code/installers/gen-setup.py | python3 -

    # Install from GitHub private repo (token via env var)
    GITHUB_TOKEN=ghp_xxx python gen-setup.py

    # Install from GitHub private repo (token via flag)
    python gen-setup.py --github-token ghp_xxx

    # Install from local disk clone (corporate / air-gapped)
    python gen-setup.py --source /path/to/ai_sdlc_method

    # Install to a specific directory
    python gen-setup.py --target /path/to/project

    # Plugin only (no workspace)
    python gen-setup.py --no-workspace

    # Preview changes without writing
    python gen-setup.py --dry-run

    # Verify existing installation
    python gen-setup.py verify

What gets created:
    .claude/settings.json          - Marketplace + plugin registration
    .ai-workspace/                 - v2 workspace
        events/events.jsonl        - Event log (append-only)
        features/active/           - Active feature vectors
        features/completed/        - Converged feature vectors
        graph/graph_topology.yml   - Asset graph topology (REQ-TOOL-007, REQ-TOOL-014)
        spec/                      - Derived spec views
        tasks/active/              - Task tracking
        tasks/finished/            - Completed tasks
        context/project_constraints.yml - Project constraints (with structure section)
        agents/                    - Per-agent working state
    specification/                 - Spec directory (if absent)
        INTENT.md                  - Intent template
"""

import sys
import os
import json
import argparse
import shutil
import subprocess
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple


# =============================================================================
# Configuration
# =============================================================================

GITHUB_REPO = "foolishimp/ai_sdlc_method"
PLUGIN_NAME = "genesis"
MARKETPLACE_NAME = "genesis"
PLUGIN_BASE = "imp_claude/code/.claude-plugin/plugins/genesis"

# Repo-relative paths (used for both GitHub and local disk source modes)
PLUGIN_JSON_PATH = f"{PLUGIN_BASE}/plugin.json"
GRAPH_TOPOLOGY_PATH = f"{PLUGIN_BASE}/config/graph_topology.yml"
BOOTLOADER_PATH = "specification/core/GENESIS_BOOTLOADER.md"
COMMANDS_BASE_PATH = f"{PLUGIN_BASE}/commands"
ENGINE_BASE_PATH = "imp_claude/code/genesis"
EDGE_PARAMS_BASE_PATH = f"{PLUGIN_BASE}/config/edge_params"
HOOKS_BASE_PATH = f"{PLUGIN_BASE}/hooks"

# Legacy URL constants (kept for backward compat — derived from repo-relative paths)
PLUGIN_JSON_URL = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{PLUGIN_JSON_PATH}"
GRAPH_TOPOLOGY_URL = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{GRAPH_TOPOLOGY_PATH}"
BOOTLOADER_URL = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{BOOTLOADER_PATH}"
COMMANDS_URL_BASE = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{COMMANDS_BASE_PATH}"
ENGINE_URL_BASE = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{ENGINE_BASE_PATH}"

COMMANDS = [
    "gen-checkpoint", "gen-escalate", "gen-gaps", "gen-init",
    "gen-iterate", "gen-release", "gen-review", "gen-spawn",
    "gen-spec-review", "gen-start", "gen-status", "gen-trace", "gen-zoom",
    "gen-comment", "gen-consensus-open", "gen-consensus-recover",
    "gen-dispose", "gen-review-proposal", "gen-vote",
]

ENGINE_FILES = [
    "__init__.py", "__main__.py", "config_loader.py", "consensus_engine.py",
    "contracts.py", "dispatch.py", "dispatch_loop.py", "dispatch_monitor.py", "edge_runner.py",
    "engine.py", "fd_classify.py", "fd_emit.py", "fd_evaluate.py",
    "fd_route.py", "fd_sense.py", "fd_spawn.py", "feature_parallelism.py",
    "feature_view.py", "fp_functor.py", "functor.py", "human_audit.py",
    "intent_observer.py", "models.py", "ol_event.py", "outcome_types.py", "proc.py",
    "role_authority.py", "schema_discovery.py", "serialiser.py",
    "spec_boundary.py", "workspace_analysis.py", "workspace_gradient.py",
    "workspace_integrity.py", "workspace_repair.py", "workspace_state.py",
]

ENGINE_SCRIPTS = [
    "scripts/migrate_events_v1_to_v2.py",
]

EDGE_PARAMS_FILES = [
    "adr.yml", "bdd.yml", "code_tagging.yml",
    "composition_consensus.yml", "composition_review.yml",
    "design_code.yml", "design_module_decomp.yml", "design_tests.yml",
    "feature_decomp_design_rec.yml", "feedback_loop.yml",
    "intent_dispatch.yml", "intent_requirements.yml",
    "module_decomp_basis_proj.yml", "requirements_design.yml",
    "requirements_feature_decomp.yml", "schema_discovery.yml",
    "tdd.yml", "traceability.yml", "workspace_analysis.yml",
]

POST_COMMIT_HOOK_SCRIPT = "post-commit-spec-watch.sh"

BOOTLOADER_START_MARKER = "<!-- GENESIS_BOOTLOADER_START -->"
BOOTLOADER_END_MARKER = "<!-- GENESIS_BOOTLOADER_END -->"

VERSION = "3.0.11"


# =============================================================================
# Source Configuration — 3 modes for GitHub public, GitHub private, local disk
# =============================================================================

@dataclass
class SourceConfig:
    """Unified source configuration for fetching installer assets.

    Three modes:
      github-public   — unauthenticated raw.githubusercontent.com (default)
      github-token    — token-authenticated GitHub (private repos, rate-limited CI)
      local           — read from a local clone of ai_sdlc_method (air-gapped / corporate)
    """
    mode: str                        # "github-public" | "github-token" | "local"
    token: str = ""                  # GitHub token (github-token mode only)
    local_path: Optional[Path] = None  # Repo root path (local mode only)
    branch: str = "main"             # GitHub branch (github modes only)

    def describe(self) -> str:
        if self.mode == "local":
            return f"local:{self.local_path}"
        if self.mode == "github-token":
            masked = f"{self.token[:4]}***" if self.token else "???"
            return f"github:{GITHUB_REPO}@{self.branch} (token {masked})"
        return f"github:{GITHUB_REPO}@{self.branch}"


def fetch_asset(source_config: SourceConfig, repo_relative_path: str, timeout: int = 10) -> str:
    """Fetch a single asset by repo-relative path.

    Dispatches to local filesystem read or authenticated/unauthenticated HTTP
    depending on source_config.mode.
    """
    if source_config.mode == "local":
        if source_config.local_path is None:
            raise ValueError("local_path must be set for local source mode")
        full_path = source_config.local_path / repo_relative_path
        if not full_path.exists():
            raise FileNotFoundError(f"Local asset not found: {full_path}")
        return full_path.read_text(encoding="utf-8")

    # GitHub modes (public or token-authenticated)
    url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{source_config.branch}/{repo_relative_path}"
    req = urllib.request.Request(url)
    if source_config.token:
        req.add_header("Authorization", f"token {source_config.token}")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8")


def build_source_config(args) -> SourceConfig:
    """Build SourceConfig from CLI args and environment.

    Priority (first match wins):
      1. --source PATH        → local mode
      2. --github-token TOKEN → github-token mode
      3. GITHUB_TOKEN env var → github-token mode
      4. gh auth token CLI    → github-token mode
      5. (default)            → github-public mode
    """
    branch = getattr(args, "branch", "main") or "main"

    # 1. Local disk mode
    local_source = getattr(args, "source", None)
    if local_source:
        local_path = Path(local_source).expanduser().resolve()
        if not local_path.is_dir():
            print_warn(f"--source path does not exist or is not a directory: {local_path}")
        return SourceConfig(mode="local", local_path=local_path, branch=branch)

    # 2. Explicit CLI token
    token = getattr(args, "github_token", None)
    if token:
        return SourceConfig(mode="github-token", token=token, branch=branch)

    # 3. GITHUB_TOKEN environment variable
    env_token = os.environ.get("GITHUB_TOKEN", "").strip()
    if env_token:
        return SourceConfig(mode="github-token", token=env_token, branch=branch)

    # 4. gh CLI token (works for already-authenticated users)
    gh_token = _get_gh_token()
    if gh_token:
        return SourceConfig(mode="github-token", token=gh_token, branch=branch)

    # 5. Default: public unauthenticated
    return SourceConfig(mode="github-public", branch=branch)


def _get_gh_token() -> str:
    """Get GitHub token from the gh CLI (silent — no output if not installed)."""
    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return ""


# =============================================================================
# Workspace Templates
# =============================================================================

PROJECT_CONSTRAINTS_TEMPLATE = """\
# Project Constraints — {project_name}
# Implements: REQ-CTX-001 (Context as Constraint Surface)
# Generated by gen-setup.py — fill in during requirements→design edge

project:
  name: "{project_name}"
  kind: ""           # application | library | service | data-pipeline
  language: ""       # auto-detected or user-specified
  test_runner: ""    # auto-detected or user-specified

# Mandatory dimensions (required at requirements→design edge)
constraints:
  ecosystem_compatibility:
    language: ""
    version: ""
    runtime: ""
    frameworks: []
  deployment_target:
    platform: ""
    cloud_provider: ""
    environment_tiers: []
  security_model:
    authentication: ""
    authorisation: ""
    data_protection: ""
  build_system:
    tool: ""
    module_structure: ""
    ci_integration: ""

  # Advisory dimensions (optional, fill when known)
  data_governance:
    classification: ""
    retention: ""
    regulations: []
  performance_envelope:
    p99_latency_ms: null
    throughput_rps: null
  observability:
    logging: ""
    metrics: ""
    tracing: ""
  error_handling:
    strategy: ""     # fail-fast | retry | circuit-breaker

# Multi-tenant folder structure (REQ-TOOL-012, REQ-TOOL-013)
# Controls where design→code edge places generated source code.
# Each design variant gets its own imp_<name>/ directory.
structure:
  design_tenants:
    # - name: ""               # e.g., "scala_spark", "python_django"
    #   output_dir: ""         # e.g., "imp_scala_spark/"
    #   description: ""        # e.g., "Scala 2.13 + Spark 3.5 implementation"
  root_code_policy: reject     # reject | warn — whether source code at project root is allowed

tools:
  check_tags:
    source_path: "src"          # path checked for Implements: REQ-* tags
    tests_path: "tests"         # path checked for Validates: REQ-* tags
    tests_exclude: "__init__.py __pycache__"  # space-separated exclusions
"""

INTENT_TEMPLATE = """\
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

---

## Business Value

<!-- Why does this matter? Who benefits? -->

---

## Success Criteria

- [ ] Criterion 1
- [ ] Criterion 2

---
"""

ACTIVE_TASKS_TEMPLATE = """\
# Active Tasks

*Last Updated: {date}*

---

No active tasks. Run `/gen-start` to begin.
"""


# =============================================================================
# Helper Functions
# =============================================================================

def print_banner(title: str, version: str = ""):
    """Print setup banner."""
    print()
    print("+" + "=" * 62 + "+")
    title_line = f"AI SDLC Method v2 - {title}"
    padding = (62 - len(title_line)) // 2
    print("|" + " " * padding + title_line + " " * (62 - padding - len(title_line)) + "|")
    if version:
        version_line = f"Version: {version}"
        padding = (62 - len(version_line)) // 2
        print("|" + " " * padding + version_line + " " * (62 - padding - len(version_line)) + "|")
    print("+" + "=" * 62 + "+")
    print()


def print_ok(msg: str):
    print(f"  [OK] {msg}")


def print_error(msg: str):
    print(f"  [ERROR] {msg}")


def print_info(msg: str):
    print(f"  {msg}")


def print_warn(msg: str):
    print(f"  [WARN] {msg}")


def get_github_token() -> str:
    """Get GitHub token (env var preferred, then gh CLI). Kept for backward compat."""
    env_token = os.environ.get("GITHUB_TOKEN", "").strip()
    if env_token:
        return env_token
    return _get_gh_token()


def fetch_url(url: str, timeout: int = 10) -> str:
    """Fetch URL with optional GitHub token auth. Kept for backward compat."""
    token = get_github_token()
    req = urllib.request.Request(url)
    if token and "raw.githubusercontent.com" in url:
        req.add_header("Authorization", f"token {token}")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8")


def get_plugin_version(source_config: Optional[SourceConfig] = None) -> str:
    """Fetch the latest plugin version from the configured source."""
    try:
        if source_config is not None:
            data = json.loads(fetch_asset(source_config, PLUGIN_JSON_PATH, timeout=5))
        else:
            data = json.loads(fetch_url(PLUGIN_JSON_URL, timeout=5))
        return data.get("version", "unknown")
    except Exception:
        return VERSION


def write_file(path: Path, content: str, dry_run: bool, force: bool = False) -> bool:
    """Write file if it doesn't exist (or force is True). Returns True on success."""
    if path.exists() and not force:
        print_info(f"Exists: {path.relative_to(path.parent.parent) if len(path.parts) > 2 else path}")
        return True

    if dry_run:
        print_info(f"Would create: {path}")
        return True

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        f.write(content)
    print_ok(f"Created {path}")
    return True


def detect_project_name(target: Path) -> str:
    """Auto-detect project name from directory or config files."""
    # Try pyproject.toml
    pyproject = target / "pyproject.toml"
    if pyproject.exists():
        try:
            content = pyproject.read_text()
            for line in content.splitlines():
                if line.strip().startswith("name"):
                    _, _, val = line.partition("=")
                    return val.strip().strip('"').strip("'")
        except Exception:
            pass

    # Try package.json
    pkg = target / "package.json"
    if pkg.exists():
        try:
            data = json.loads(pkg.read_text())
            return data.get("name", target.name)
        except Exception:
            pass

    # Fallback to directory name
    return target.name


# =============================================================================
# Plugin Configuration
# =============================================================================

def clear_plugin_cache(dry_run: bool) -> bool:
    """Clear cached plugin to ensure latest version is fetched."""
    cache_locations = [
        Path.home() / ".claude" / "plugins" / "marketplaces" / MARKETPLACE_NAME,
        Path.home() / ".claude" / "plugins" / "cache" / MARKETPLACE_NAME / PLUGIN_NAME,
        # Legacy cache from pre-genesis installs
        Path.home() / ".claude" / "plugins" / "marketplaces" / "aisdlc",
        Path.home() / ".claude" / "plugins" / "cache" / "aisdlc" / "gen-methodology-v2",
        # Legacy cache from genisis typo era
        Path.home() / ".claude" / "plugins" / "marketplaces" / "genisis",
        Path.home() / ".claude" / "plugins" / "cache" / "genisis" / "genisis",
    ]

    found_any = False
    for cache_dir in cache_locations:
        if not cache_dir.exists():
            continue
        found_any = True
        if dry_run:
            print_info(f"Would remove: {cache_dir}")
            continue
        try:
            shutil.rmtree(cache_dir)
            print_ok(f"Cleared: {cache_dir}")
        except Exception as e:
            print_warn(f"Could not clear {cache_dir}: {e}")

    if not found_any:
        print_info("No cached plugin found (fresh install)")

    # Clean stale keys from global plugin registry files
    legacy_keys_marketplace = ["aisdlc", "genisis"]
    legacy_keys_plugin = ["gen-methodology-v2@aisdlc", "genisis@genisis"]

    km_path = Path.home() / ".claude" / "plugins" / "known_marketplaces.json"
    if km_path.exists():
        try:
            km = json.loads(km_path.read_text())
            dirty = False
            for key in legacy_keys_marketplace:
                if key in km:
                    if dry_run:
                        print_info(f"Would remove '{key}' from known_marketplaces.json")
                    else:
                        km.pop(key)
                        dirty = True
            if dirty:
                km_path.write_text(json.dumps(km, indent=2))
                print_ok("Cleaned legacy keys from known_marketplaces.json")
        except Exception as e:
            print_warn(f"Could not clean known_marketplaces.json: {e}")

    ip_path = Path.home() / ".claude" / "plugins" / "installed_plugins.json"
    if ip_path.exists():
        try:
            ip = json.loads(ip_path.read_text())
            plugins = ip.get("plugins", {})
            dirty = False
            for key in legacy_keys_plugin:
                if key in plugins:
                    if dry_run:
                        print_info(f"Would remove '{key}' from installed_plugins.json")
                    else:
                        plugins.pop(key)
                        dirty = True
            if dirty:
                ip_path.write_text(json.dumps(ip, indent=2))
                print_ok("Cleaned legacy keys from installed_plugins.json")
        except Exception as e:
            print_warn(f"Could not clean installed_plugins.json: {e}")

    return True


def setup_settings(target: Path, dry_run: bool) -> bool:
    """Create or update .claude/settings.json with marketplace and plugin."""
    settings_file = target / ".claude" / "settings.json"

    existing = {}
    if settings_file.exists():
        try:
            with open(settings_file, "r") as f:
                existing = json.load(f)
        except json.JSONDecodeError:
            print_warn("Existing settings.json has invalid JSON, will merge carefully")

    # Add marketplace (and remove legacy keys from pre-genesis installs)
    if "extraKnownMarketplaces" not in existing:
        existing["extraKnownMarketplaces"] = {}
    existing["extraKnownMarketplaces"].pop("aisdlc", None)
    existing["extraKnownMarketplaces"].pop("genisis", None)
    existing["extraKnownMarketplaces"][MARKETPLACE_NAME] = {
        "source": {"source": "github", "repo": GITHUB_REPO}
    }

    # Enable plugin (hooks are loaded from the plugin's hooks.json by Claude Code)
    if "enabledPlugins" not in existing:
        existing["enabledPlugins"] = {}
    existing["enabledPlugins"].pop("gen-methodology-v2@aisdlc", None)
    existing["enabledPlugins"].pop("genisis@genisis", None)
    existing["enabledPlugins"][f"{PLUGIN_NAME}@{MARKETPLACE_NAME}"] = True

    if dry_run:
        print_info(f"Would create: {settings_file}")
        return True

    settings_file.parent.mkdir(parents=True, exist_ok=True)
    with open(settings_file, "w") as f:
        json.dump(existing, f, indent=2)
    print_ok(f"Created {settings_file}")
    return True


# =============================================================================
# Workspace Setup (v2 structure)
# =============================================================================

def setup_workspace(target: Path, project_name: str, dry_run: bool,
                    source_config: Optional[SourceConfig] = None) -> bool:
    """Create .ai-workspace/ with v2 structure."""
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d %H:%M")
    iso_ts = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    ws = target / ".ai-workspace"

    # Directory structure
    # Context lineage directories (ADR-S-022 §2): methodology → org → policy → domain → prior → project
    _lineage_levels = ("methodology", "org", "policy", "domain", "prior", "project")
    dirs = [
        ws / "events",
        ws / "features" / "active",
        ws / "features" / "completed",
        ws / "graph",
        ws / "spec",
        ws / "tasks" / "active",
        ws / "tasks" / "finished",
        ws / "agents",
        # 6-level lineage context scopes
        *[ws / "context" / level for level in _lineage_levels],
    ]

    for d in dirs:
        if dry_run:
            if not d.exists():
                print_info(f"Would create dir: {d.relative_to(target)}")
        else:
            d.mkdir(parents=True, exist_ok=True)

    # Files
    files = {
        ws / "events" / "events.jsonl": "",  # empty — first event appended below
        ws / "tasks" / "active" / "ACTIVE_TASKS.md": ACTIVE_TASKS_TEMPLATE.format(date=date_str),
        ws / "tasks" / "finished" / ".gitkeep": "",
        ws / "features" / "active" / ".gitkeep": "",
        ws / "features" / "completed" / ".gitkeep": "",
        ws / "agents" / ".gitkeep": "",
        ws / "spec" / ".gitkeep": "",
    }

    for path, content in files.items():
        write_file(path, content, dry_run)

    # Project constraints template
    constraints_path = ws / "context" / "project_constraints.yml"
    write_file(
        constraints_path,
        PROJECT_CONSTRAINTS_TEMPLATE.format(project_name=project_name),
        dry_run,
    )

    # Graph topology (REQ-TOOL-007, REQ-TOOL-014 — observability integration contract)
    graph_topology_path = ws / "graph" / "graph_topology.yml"
    if not graph_topology_path.exists():
        if dry_run:
            print_info("Would fetch and create: .ai-workspace/graph/graph_topology.yml")
        else:
            topology_content = _fetch_graph_topology(source_config)
            if topology_content:
                write_file(graph_topology_path, topology_content, dry_run)
            else:
                print_warn("Could not fetch graph_topology.yml — create manually or re-run with network")
    else:
        print_info("Exists: .ai-workspace/graph/graph_topology.yml")

    # Emit project_initialized event (idempotent — only if events.jsonl is empty)
    events_file = ws / "events" / "events.jsonl"
    if not dry_run:
        if events_file.exists() and events_file.stat().st_size > 0:
            print_info("events.jsonl already has events — skipping project_initialized")
        else:
            event = {
                "event_type": "project_initialized",
                "timestamp": iso_ts,
                "project": project_name,
                "data": {
                    "method_version": VERSION,
                    "installer": "gen-setup.py",
                    "workspace_structure": "v2",
                    "lineage_levels": list(_lineage_levels),  # ADR-S-022 §2 provenance
                },
            }
            with open(events_file, "a") as f:
                f.write(json.dumps(event) + "\n")
            print_ok("Emitted project_initialized event")
    else:
        print_info("Would emit project_initialized event")

    return True


def _fetch_graph_topology(source_config: Optional[SourceConfig]) -> str:
    """Fetch graph_topology.yml — uses source_config if provided, else legacy fallback."""
    if source_config is not None:
        try:
            return fetch_asset(source_config, GRAPH_TOPOLOGY_PATH, timeout=10)
        except Exception as e:
            print_warn(f"Could not fetch graph_topology.yml from source: {e}")
            return ""

    # Legacy path: try GitHub, then local development fallback
    try:
        return fetch_url(GRAPH_TOPOLOGY_URL, timeout=10)
    except Exception:
        pass
    local_path = Path(__file__).parent.parent / ".claude-plugin" / "plugins" / "genesis" / "config" / "graph_topology.yml"
    if local_path.exists():
        return local_path.read_text()
    return ""


def _fetch_bootloader(source_config: Optional[SourceConfig]) -> str:
    """Fetch GENESIS_BOOTLOADER.md — uses source_config if provided, else legacy fallback."""
    if source_config is not None:
        try:
            return fetch_asset(source_config, BOOTLOADER_PATH, timeout=10)
        except Exception as e:
            print_warn(f"Could not fetch GENESIS_BOOTLOADER.md from source: {e}")
            return ""

    # Legacy path: try GitHub, then local development fallback
    try:
        return fetch_url(BOOTLOADER_URL, timeout=10)
    except Exception:
        pass
    local_path = Path(__file__).resolve().parent.parent.parent.parent / "specification" / "core" / "GENESIS_BOOTLOADER.md"
    if local_path.exists():
        return local_path.read_text()
    return ""


def setup_commands(target: Path, dry_run: bool,
                   source_config: Optional[SourceConfig] = None) -> bool:
    """Fetch /gen-* commands into .claude/commands/."""
    commands_dir = target / ".claude" / "commands"

    if dry_run:
        src_desc = source_config.describe() if source_config else f"github:{GITHUB_REPO}@main"
        print_info(f"Would fetch {len(COMMANDS)} commands from {src_desc}")
        return True

    commands_dir.mkdir(parents=True, exist_ok=True)
    failed = []
    for cmd in COMMANDS:
        rel_path = f"{COMMANDS_BASE_PATH}/{cmd}.md"
        try:
            if source_config is not None:
                content = fetch_asset(source_config, rel_path, timeout=10)
            else:
                content = fetch_url(f"{COMMANDS_URL_BASE}/{cmd}.md", timeout=10)
            dest = commands_dir / f"{cmd}.md"
            dest.unlink(missing_ok=True)
            dest.write_text(content)
        except Exception as e:
            print_warn(f"Could not fetch {cmd}.md: {e}")
            failed.append(cmd)
    installed = len(COMMANDS) - len(failed)
    print_ok(f"Installed {installed}/{len(COMMANDS)} commands")
    if failed:
        print_warn(f"Failed: {', '.join(failed)}")

    # Write version stamp
    src_desc = source_config.describe() if source_config else f"github:{GITHUB_REPO}@main"
    stamp = commands_dir / ".genesis-installed"
    stamp.write_text(
        f"version: {VERSION}\n"
        f"installed: {datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')}\n"
        f"source: {src_desc}\n"
    )

    return True


def setup_engine(target: Path, dry_run: bool,
                 source_config: Optional[SourceConfig] = None) -> bool:
    """Fetch genesis engine source into .genesis/genesis/.

    Installed at: .genesis/genesis/
    Invoked as:   PYTHONPATH=.genesis python -m genesis evaluate ...
    """
    engine_dir = target / ".genesis" / "genesis"

    if dry_run:
        src_desc = source_config.describe() if source_config else f"github:{GITHUB_REPO}@main"
        print_info(f"Would fetch {len(ENGINE_FILES)} engine files from {src_desc} → .genesis/genesis/")
        return True

    engine_dir.mkdir(parents=True, exist_ok=True)
    (engine_dir / "scripts").mkdir(exist_ok=True)
    edge_params_dir = engine_dir / "config" / "edge_params"
    edge_params_dir.mkdir(parents=True, exist_ok=True)

    failed = []
    for filename in ENGINE_FILES + ENGINE_SCRIPTS:
        rel_path = f"{ENGINE_BASE_PATH}/{filename}"
        try:
            if source_config is not None:
                content = fetch_asset(source_config, rel_path, timeout=10)
            else:
                content = fetch_url(f"{ENGINE_URL_BASE}/{filename}", timeout=10)
            dest = engine_dir / filename
            dest.unlink(missing_ok=True)
            dest.write_text(content)
        except Exception as e:
            print_warn(f"Could not fetch {filename}: {e}")
            failed.append(filename)

    # Install edge_params configs — required by the engine for deterministic evaluation
    edge_params_failed = []
    for filename in EDGE_PARAMS_FILES:
        rel_path = f"{EDGE_PARAMS_BASE_PATH}/{filename}"
        try:
            if source_config is not None:
                content = fetch_asset(source_config, rel_path, timeout=10)
            else:
                content = fetch_url(
                    f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{rel_path}",
                    timeout=10,
                )
            dest = edge_params_dir / filename
            dest.unlink(missing_ok=True)
            dest.write_text(content)
        except Exception as e:
            print_warn(f"Could not fetch edge_params/{filename}: {e}")
            edge_params_failed.append(filename)

    installed = len(ENGINE_FILES) + len(ENGINE_SCRIPTS) - len(failed)
    total = len(ENGINE_FILES) + len(ENGINE_SCRIPTS)
    ep_installed = len(EDGE_PARAMS_FILES) - len(edge_params_failed)
    print_ok(f"Installed {installed}/{total} engine files → .genesis/genesis/")
    print_ok(f"Installed {ep_installed}/{len(EDGE_PARAMS_FILES)} edge_params configs → .genesis/genesis/config/edge_params/")
    if failed:
        print_warn(f"Failed engine files: {', '.join(failed)}")
    if edge_params_failed:
        print_warn(f"Failed edge_params: {', '.join(edge_params_failed)}")

    return True


def setup_bootloader(target: Path, dry_run: bool,
                     source_config: Optional[SourceConfig] = None) -> bool:
    """Install or replace Genesis Bootloader in CLAUDE.md (always upgrades)."""
    claude_md = target / "CLAUDE.md"

    bootloader = _fetch_bootloader(source_config)
    if not bootloader:
        print_warn("Could not fetch GENESIS_BOOTLOADER.md — bootloader not installed")
        return False

    existing = claude_md.read_text() if claude_md.exists() else ""

    if dry_run:
        if BOOTLOADER_START_MARKER in existing:
            print_info("Would replace Genesis Bootloader in CLAUDE.md")
        elif existing:
            print_info("Would append Genesis Bootloader to existing CLAUDE.md")
        else:
            print_info("Would create CLAUDE.md with Genesis Bootloader")
        return True

    bootloader_section = f"{BOOTLOADER_START_MARKER}\n{bootloader}\n{BOOTLOADER_END_MARKER}\n"

    if BOOTLOADER_START_MARKER in existing:
        import re
        pattern = re.compile(
            re.escape(BOOTLOADER_START_MARKER) + r".*?" + re.escape(BOOTLOADER_END_MARKER) + r"\n?",
            re.DOTALL,
        )
        updated = pattern.sub(bootloader_section, existing)
        claude_md.write_text(updated)
        print_ok(f"Updated Genesis Bootloader in CLAUDE.md")
    elif existing.strip():
        with open(claude_md, "a") as f:
            f.write(f"\n\n---\n\n{bootloader_section}")
        print_ok("Appended Genesis Bootloader to CLAUDE.md")
    else:
        claude_md.write_text(bootloader_section)
        print_ok("Created CLAUDE.md with Genesis Bootloader")

    return True


def setup_git_hooks(target: Path, dry_run: bool,
                    source_config: Optional[SourceConfig] = None) -> bool:
    """Install post-commit-spec-watch.sh into .git/hooks/post-commit (REQ-EVOL-004).

    Only runs if .git/ exists in target. Non-destructive — appends a call to the
    hook script rather than replacing an existing post-commit hook. Idempotent.
    """
    git_dir = target / ".git"
    if not git_dir.is_dir():
        print_info("No .git/ found — skipping git hooks install")
        return True  # not an error for non-git projects

    hooks_dir = git_dir / "hooks"
    hook_file = hooks_dir / "post-commit"
    hook_script_name = POST_COMMIT_HOOK_SCRIPT
    genesis_hook_dest = target / ".claude" / "genesis" / "hooks" / hook_script_name
    hook_rel_path = f"{HOOKS_BASE_PATH}/{hook_script_name}"

    if dry_run:
        if genesis_hook_dest.exists():
            print_info(f"Would update: .claude/genesis/hooks/{hook_script_name}")
        else:
            print_info(f"Would fetch: {hook_script_name} → .claude/genesis/hooks/")
        if hook_file.exists():
            print_info("Would append genesis hook to existing .git/hooks/post-commit")
        else:
            print_info("Would create .git/hooks/post-commit with genesis hook")
        return True

    # Fetch the hook script
    try:
        if source_config is not None:
            hook_content = fetch_asset(source_config, hook_rel_path, timeout=10)
        else:
            hook_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{hook_rel_path}"
            with urllib.request.urlopen(hook_url, timeout=10) as resp:
                hook_content = resp.read().decode("utf-8")
    except Exception as e:
        print_warn(f"Could not fetch {hook_script_name}: {e}")
        print_warn("Skipping git hook install — run manually later")
        return True  # not fatal

    # Write to .claude/genesis/hooks/
    genesis_hook_dest.parent.mkdir(parents=True, exist_ok=True)
    genesis_hook_dest.write_text(hook_content)
    genesis_hook_dest.chmod(0o755)

    # Install/update .git/hooks/post-commit
    hooks_dir.mkdir(exist_ok=True)
    GENESIS_MARKER = "# genesis:spec-watch"

    if hook_file.exists():
        existing = hook_file.read_text()
        if GENESIS_MARKER in existing:
            print_info(".git/hooks/post-commit already has genesis hook — skipping")
            return True
        # Append to existing hook
        with open(hook_file, "a") as f:
            f.write(f"\n{GENESIS_MARKER}\n")
            f.write(f'"{genesis_hook_dest}"\n')
        print_ok("Appended genesis spec-watch to .git/hooks/post-commit")
    else:
        hook_file.write_text(
            "#!/bin/bash\n"
            f"{GENESIS_MARKER}\n"
            f'"{genesis_hook_dest}"\n'
            "exit 0\n"
        )
        hook_file.chmod(0o755)
        print_ok("Created .git/hooks/post-commit with genesis spec-watch hook")

    return True


def setup_specification(target: Path, project_name: str, dry_run: bool) -> bool:
    """Create specification/ directory with INTENT.md template if absent."""
    spec_dir = target / "specification"
    intent_file = spec_dir / "INTENT.md"

    if intent_file.exists():
        print_info(f"Exists: specification/INTENT.md")
        return True

    date_str = datetime.now().strftime("%Y-%m-%d")
    write_file(
        intent_file,
        INTENT_TEMPLATE.format(project_name=project_name, date=date_str),
        dry_run,
    )
    return True


# =============================================================================
# Verify Command
# =============================================================================

def cmd_verify(args) -> int:
    """Verify an existing installation."""
    target = Path(args.target).resolve()
    project_name = detect_project_name(target)
    print_banner("Installation Verify", VERSION)

    passed = 0
    failed = 0

    # Detect install mode: if .ai-workspace/ is absent but .claude/settings.json
    # exists, this is a --no-workspace (plugin-only) install.
    has_workspace = (target / ".ai-workspace").is_dir()
    has_settings = (target / ".claude" / "settings.json").exists()
    plugin_only = has_settings and not has_workspace

    if plugin_only:
        print_info("Detected: plugin-only install (--no-workspace)")
        print()

    # Plugin checks (always)
    checks = [
        (target / ".claude" / "settings.json", "Plugin settings"),
    ]

    # Workspace checks (only for full installs)
    if not plugin_only:
        checks += [
            (target / ".ai-workspace" / "events" / "events.jsonl", "Event log"),
            (target / ".ai-workspace" / "features" / "active", "Feature vectors dir"),
            (target / ".ai-workspace" / "graph" / "graph_topology.yml", "Graph topology"),
            (target / ".ai-workspace" / "tasks" / "active" / "ACTIVE_TASKS.md", "Task tracking"),
            (target / ".ai-workspace" / "context" / "project_constraints.yml", "Project constraints"),
        ]

    for path, label in checks:
        if path.exists():
            print_ok(f"{label}: {path.relative_to(target)}")
            passed += 1
        else:
            print_error(f"{label}: MISSING — {path.relative_to(target)}")
            failed += 1

    # Genesis Bootloader check (only for full installs)
    if not plugin_only:
        claude_md = target / "CLAUDE.md"
        if claude_md.exists():
            claude_content = claude_md.read_text()
            if BOOTLOADER_START_MARKER in claude_content:
                print_ok("Genesis Bootloader present in CLAUDE.md")
                passed += 1
            else:
                print_error("Genesis Bootloader NOT in CLAUDE.md — re-run installer")
                failed += 1
        else:
            print_error("CLAUDE.md missing — re-run installer")
            failed += 1

    # Commands check
    commands_dir = target / ".claude" / "commands"
    present = [cmd for cmd in COMMANDS if (commands_dir / f"{cmd}.md").exists()]
    if len(present) == len(COMMANDS):
        print_ok(f"Commands: {len(COMMANDS)}/{len(COMMANDS)} gen-*.md present")
        passed += 1
    else:
        missing = [cmd for cmd in COMMANDS if cmd not in present]
        print_error(f"Commands: {len(present)}/{len(COMMANDS)} present — missing: {', '.join(missing)}")
        failed += 1

    # Engine check
    engine_dir = target / ".genesis" / "genesis"
    engine_main = engine_dir / "__main__.py"
    if engine_main.exists():
        engine_files_present = sum(1 for f in ENGINE_FILES if (engine_dir / f).exists())
        print_ok(f"Engine: {engine_files_present}/{len(ENGINE_FILES)} files in .genesis/genesis/")
        print_info("  Run: PYTHONPATH=.genesis python -m genesis evaluate ...")
        passed += 1
    else:
        print_error("Engine not installed — .genesis/genesis/__main__.py missing")
        failed += 1

    # Git hook check (advisory — not all projects use git)
    git_hook = target / ".git" / "hooks" / "post-commit"
    if (target / ".git").is_dir():
        if git_hook.exists() and "genesis:spec-watch" in git_hook.read_text():
            print_ok("Git post-commit hook: spec_modified events active")
            passed += 1
        else:
            print_warn("Git post-commit hook: not installed (run installer to add REQ-EVOL-004 events)")

    # Version stamp
    stamp = commands_dir / ".genesis-installed"
    if stamp.exists():
        print_ok(f"Installed version:\n{stamp.read_text().strip()}")
    else:
        print_warn("No version stamp — run installer to record version")

    # Check settings content
    settings_file = target / ".claude" / "settings.json"
    if settings_file.exists():
        try:
            settings = json.loads(settings_file.read_text())
            mkts = settings.get("extraKnownMarketplaces", {})
            plugins = settings.get("enabledPlugins", {})

            if MARKETPLACE_NAME in mkts:
                print_ok(f"Marketplace '{MARKETPLACE_NAME}' registered")
                passed += 1
            else:
                print_error(f"Marketplace '{MARKETPLACE_NAME}' not in settings")
                failed += 1

            plugin_key = f"{PLUGIN_NAME}@{MARKETPLACE_NAME}"
            if plugins.get(plugin_key):
                print_ok(f"Plugin '{plugin_key}' enabled")
                passed += 1
            else:
                print_error(f"Plugin '{plugin_key}' not enabled")
                failed += 1

        except Exception as e:
            print_error(f"Cannot parse settings.json: {e}")
            failed += 1

    # Check events (only for full installs)
    if not plugin_only:
        events_file = target / ".ai-workspace" / "events" / "events.jsonl"
        if events_file.exists() and events_file.stat().st_size > 0:
            try:
                first_line = events_file.read_text().strip().splitlines()[0]
                evt = json.loads(first_line)
                if evt.get("event_type") == "project_initialized":
                    print_ok(f"project_initialized event present")
                    passed += 1
                else:
                    print_warn(f"First event is '{evt.get('event_type')}', not project_initialized")
            except Exception:
                print_warn("Cannot parse first event")

    print()
    print("=" * 64)
    print(f"  Checks: {passed} passed, {failed} failed")
    if failed == 0:
        print("  Installation verified OK")
        emit_install_event(
            target, project_name, VERSION, "verify",
            event_type="genesis_verified",
            extra={"checks_passed": passed, "checks_failed": failed},
        )
    else:
        print("  Installation incomplete — re-run installer to fix")
    print()

    return 0 if failed == 0 else 1


# =============================================================================
# Install Event Emission
# Implements: REQ-LIFE-002 (Telemetry and Homeostasis), REQ-SUPV-003 (Failure Observability)
# Implements: REQ-TOOL-011 (Installability)
# =============================================================================


def emit_install_event(
    target: Path,
    project_name: str,
    version: str,
    source_desc: str,
    event_type: str = "genesis_installed",
    extra: Optional[dict] = None,
) -> None:
    """Append a genesis_installed or genesis_verified event to events.jsonl.

    Called at the end of every successful install and verify run so the
    event stream carries a complete deployment + verification history.
    On first install this is the first event (before project_initialized).
    """
    import datetime as _dt

    events_file = target / ".ai-workspace" / "events" / "events.jsonl"
    if not events_file.exists():
        return  # workspace not set up (plugin-only mode) — skip

    engine_dir = target / ".genesis" / "genesis"
    engine_files = sum(1 for f in ENGINE_FILES if (engine_dir / f).exists())

    edge_params_dir = engine_dir / "config" / "edge_params"
    edge_params = sum(1 for f in EDGE_PARAMS_FILES if (edge_params_dir / f).exists()) if edge_params_dir.exists() else 0

    commands_dir = target / ".claude" / "commands"
    commands = sum(1 for cmd in COMMANDS if (commands_dir / f"{cmd}.md").exists())

    now = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    data: dict = {
        "version": version,
        "source": source_desc,
        "engine_files": engine_files,
        "edge_params": edge_params,
        "commands": commands,
    }
    if extra:
        data.update(extra)

    event = {
        "event_type": event_type,
        "timestamp": now,
        "project": project_name,
        "data": data,
    }
    with open(events_file, "a") as f:
        f.write(json.dumps(event) + "\n")


# =============================================================================
# Default Command — Install
# =============================================================================

def cmd_install(args) -> int:
    """Default command: plugin + workspace setup."""
    target = Path(args.target).resolve()
    project_name = detect_project_name(target)

    # REQ-TOOL-015 AC-2: warn when installing inside an imp_* tenant directory
    import re as _re
    if _re.search(r'[/\\]imp_[^/\\]+$', str(target)):
        print_warn(
            f"WARNING: target directory '{target.name}' looks like an implementation "
            f"tenant (imp_*/).\n"
            f"  The workspace will be scoped to this directory only and will NOT span\n"
            f"  specification/ or sibling imp_*/ tenants.\n"
            f"  To monitor the full project, run the installer from the project root\n"
            f"  (the directory containing specification/ and imp_*/)."
        )
        print()

    # Build source configuration
    source_config = build_source_config(args)

    version = get_plugin_version(source_config)
    print_banner("Project Setup", version)

    print_info(f"Target:  {target}")
    print_info(f"Project: {project_name}")
    print_info(f"Plugin:  {PLUGIN_NAME} v{version}")
    print_info(f"Source:  {source_config.describe()}")
    print_info(f"Workspace: {'No' if args.no_workspace else 'Yes (v2 structure)'}")
    if args.dry_run:
        print_warn("DRY RUN — no changes will be made")
    print()

    success = True

    # 1. Clear plugin cache
    print("--- Plugin Cache ---")
    clear_plugin_cache(args.dry_run)
    print()

    # 2. Configure plugin (marketplace + enablement; hooks come from plugin)
    print("--- Plugin Configuration ---")
    if not setup_settings(target, args.dry_run):
        success = False
    print()

    # 2b. Install /gen-* commands (non-fatal — source may be temporarily unavailable)
    print("--- Commands ---")
    setup_commands(target, args.dry_run, source_config)
    print()

    # 2c. Install genesis engine (non-fatal)
    print("--- Engine ---")
    setup_engine(target, args.dry_run, source_config)
    print()

    # 3. Create workspace
    if not args.no_workspace:
        print("--- Workspace (v2) ---")
        if not setup_workspace(target, project_name, args.dry_run, source_config):
            success = False
        print()

        print("--- Specification ---")
        if not setup_specification(target, project_name, args.dry_run):
            success = False
        print()

        # 3b. Append bootloader to CLAUDE.md (non-fatal)
        print("--- Genesis Bootloader ---")
        setup_bootloader(target, args.dry_run, source_config)
        print()

        # 3c. Install git post-commit hook (non-fatal — no .git in tmp dirs)
        print("--- Git Hooks ---")
        setup_git_hooks(target, args.dry_run, source_config)
        print()

    # Summary
    print("=" * 64)
    if args.dry_run:
        print("  Dry run complete — no changes made")
    elif success:
        emit_install_event(
            target, project_name, version, source_config.describe(),
            event_type="genesis_installed",
            extra={"workspace_created": not args.no_workspace},
        )
        print("  Setup complete!")
        print()
        print("  What was created:")
        print("    .claude/settings.json          Plugin config (GitHub marketplace)")
        print("    .claude/commands/gen-*.md      Slash commands")
        print("    .genesis/genesis/              Engine source (PYTHONPATH=.genesis python -m genesis)")
        if not args.no_workspace:
            print("    .ai-workspace/events/          Event log (source of truth)")
            print("    .ai-workspace/features/        Feature vector storage")
            print("    .ai-workspace/graph/           Graph topology (monitor integration)")
            print("    .ai-workspace/tasks/           Task tracking")
            print("    .ai-workspace/context/         Project constraints (with structure)")
            print("    specification/INTENT.md        Intent template")
            print("    CLAUDE.md                      Genesis Bootloader (appended)")
        print()
        print("  Next steps:")
        print("    1. Start Claude Code (it will prompt to install the marketplace)")
        print("    2. Run /plugin install genesis@genesis")
        print("    3. Run /gen-start to begin")
        print()
        print("  Verify installation:")
        print("    python gen-setup.py verify")
    else:
        print("  Setup completed with errors")
    print()

    return 0 if success else 1


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="AI SDLC Method v2 — Project Setup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Source modes:
  GitHub public (default):
    curl -sL https://raw.githubusercontent.com/.../gen-setup.py | python3 -
    python gen-setup.py

  GitHub private / authenticated:
    GITHUB_TOKEN=ghp_xxx python gen-setup.py
    python gen-setup.py --github-token ghp_xxx

  Local disk clone (corporate / air-gapped):
    python gen-setup.py --source /path/to/ai_sdlc_method

Other options:
  python gen-setup.py --target /path/to/project   Install to a specific directory
  python gen-setup.py --dry-run                   Preview changes without writing
  python gen-setup.py verify                      Verify existing installation
""",
    )

    subparsers = parser.add_subparsers(dest="command")

    # Verify subcommand
    verify_parser = subparsers.add_parser("verify", help="Verify existing installation")
    verify_parser.add_argument("--target", default=".", help="Target directory")

    # Default command arguments
    parser.add_argument("--target", default=".", help="Target directory (default: current directory)")
    parser.add_argument("--no-workspace", action="store_true", help="Skip .ai-workspace/ creation")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing")

    # Source mode arguments
    source_group = parser.add_argument_group("source mode (mutually exclusive)")
    source_group.add_argument(
        "--source",
        metavar="PATH",
        help="Local disk path to ai_sdlc_method clone (corporate / air-gapped installs)",
    )
    source_group.add_argument(
        "--github-token",
        metavar="TOKEN",
        help="GitHub personal access token for private repo access (or set GITHUB_TOKEN env var)",
    )
    source_group.add_argument(
        "--branch",
        default="main",
        metavar="BRANCH",
        help="GitHub branch to install from (default: main)",
    )

    args = parser.parse_args()

    if args.command == "verify":
        return cmd_verify(args)
    else:
        return cmd_install(args)


if __name__ == "__main__":
    sys.exit(main())
