import sys
from pathlib import Path

# Add imp_gemini to sys.path
sys.path.append(str(Path.cwd() / "imp_gemini"))

from gemini_cli.commands.commit import CommitCommand
from gemini_cli.engine.iterate import IterateEngine

def main():
    workspace_root = Path.cwd() / "imp_gemini" / ".ai-workspace"
    project_root = Path.cwd() / "imp_gemini"
    
    engine = IterateEngine(functor_map={}, project_root=project_root)
    cmd = CommitCommand(workspace_root=workspace_root, project_root=project_root)
    
    print("  [TEST] Phase 1: Checking current integrity...")
    gaps = engine.detect_integrity_gaps()
    print(f"  [TEST] Initial gaps: {len(gaps)}")
    
    print("\n  [TEST] Phase 2: Running commit to heal gaps and abort orphaned transactions...")
    cmd.run(description="Full system recovery", heal_tx=True)
    
    print("\n  [TEST] Phase 3: Verifying integrity again...")
    gaps_after = engine.detect_integrity_gaps()
    print(f"  [TEST] Gaps after commit: {len(gaps_after)}")
    
    uncommitted = [g for g in gaps_after if g["type"] == "UNCOMMITTED_CHANGE"]
    if not uncommitted:
        print("  [TEST] SUCCESS: All uncommitted changes were committed to the ledger.")
    else:
        print(f"  [TEST] FAILED: {len(uncommitted)} uncommitted changes remain.")

if __name__ == "__main__":
    main()
