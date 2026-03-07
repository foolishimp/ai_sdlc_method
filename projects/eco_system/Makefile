# Genesis Testbed — Snapshot/Restore Environment
# Usage: make <target>

PYTHON := python3
SCRIPTS := scripts
PROJECT := project

.PHONY: help init status list restore snapshot validate clean reset-hard

help:
	@echo "Genesis Testbed — Snapshot/Restore MVP Validation Environment"
	@echo ""
	@echo "Targets:"
	@echo "  make status              Show current project workspace state and H"
	@echo "  make list                List available snapshots"
	@echo "  make restore SNAP=<name> Restore project/ from a snapshot"
	@echo "  make snapshot NAME=<name> [EDGE=<edge>] [NOTE=<note>]"
	@echo "                           Capture current project/ as a snapshot"
	@echo "  make validate [EDGE=<e>] [FEATURE=<f>]"
	@echo "                           Run F_D evaluators, report H (no Claude needed)"
	@echo "  make init                Restore to 00_installed (clean start)"
	@echo "  make reset-hard          Delete project/ entirely (requires manual re-init)"
	@echo ""
	@echo "Standard workflow:"
	@echo "  make init                         # start from clean installed state"
	@echo "  # run /gen-start in Claude Code   # iterate intent→requirements"
	@echo "  make snapshot NAME=01_requirements_done EDGE='intent→requirements'"
	@echo "  # run /gen-start again            # iterate requirements→design"
	@echo "  make snapshot NAME=02_design_done EDGE='requirements→design'"
	@echo "  make validate EDGE='code↔unit_tests'  # F_D only — no Claude"

SNAP ?= 00_installed
EDGE ?= code↔unit_tests
FEATURE ?= REQ-F-CONV-001
NAME ?= $(error NAME is required. Use: make snapshot NAME=<name>)
NOTE ?=

init: ## Restore to 00_installed snapshot (clean start)
	$(PYTHON) $(SCRIPTS)/restore.py 00_installed --force

status: ## Show current workspace state and H
	@echo "=== Current Project State ==="
	@if [ -f $(PROJECT)/.ai-workspace/events/events.jsonl ]; then \
		echo "Events: $$(wc -l < $(PROJECT)/.ai-workspace/events/events.jsonl) lines"; \
	else \
		echo "Events: none"; \
	fi
	@if [ -d $(PROJECT)/.ai-workspace/features/active ]; then \
		echo "Features: $$(ls $(PROJECT)/.ai-workspace/features/active/*.yml 2>/dev/null | wc -l) active"; \
	fi
	@$(PYTHON) -c "\
import json, sys; \
f='$(PROJECT)/.ai-workspace/events/events.jsonl'; \
T=0; V=0; \
[setattr(sys, '_', (T:=T+1) or True) or True for line in open(f).readlines() if line.strip() \
  for ev in [json.loads(line).get('_metadata',{}).get('original_data',json.loads(line))] \
  if ev.get('event_type')=='iteration_completed'] \
  if __import__('pathlib').Path(f).exists() else None; \
print(f'H={T+V}  T={T}  V={V}  (iterations + failing checks)') \
" 2>/dev/null || echo "H: (not computable — no events yet)"

list: ## List available snapshots
	$(PYTHON) $(SCRIPTS)/restore.py --list

restore: ## Restore from snapshot (SNAP=name)
	$(PYTHON) $(SCRIPTS)/restore.py $(SNAP)

snapshot: ## Capture current state as snapshot (NAME=name)
	$(PYTHON) $(SCRIPTS)/snapshot.py $(NAME) \
		$(if $(EDGE),--edge "$(EDGE)") \
		$(if $(NOTE),--note "$(NOTE)")

validate: ## Run F_D evaluators on current project (no Claude)
	$(PYTHON) $(SCRIPTS)/validate.py --edge "$(EDGE)" --feature "$(FEATURE)"

clean: ## Remove generated artifacts from project/ (keep workspace)
	rm -rf $(PROJECT)/src/__pycache__ $(PROJECT)/tests/__pycache__
	find $(PROJECT) -name "*.pyc" -delete

reset-hard: ## DANGER: Delete all of project/ (requires re-init)
	@echo "WARNING: This will delete everything in project/."
	@read -p "Type 'yes' to confirm: " ans; [ "$$ans" = "yes" ] || (echo "Aborted."; exit 1)
	rm -rf $(PROJECT)
	mkdir -p $(PROJECT)
	@echo "project/ cleared. Run 'make init' to restore from 00_installed."
