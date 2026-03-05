import sys
from pathlib import Path

# Add imp_gemini to sys.path
sys.path.append(str(Path.cwd() / "imp_gemini"))

from gemini_cli.engine.iterate import IterateEngine

def main():
    engine = IterateEngine(functor_map={}, project_root=Path.cwd() / "imp_gemini")
    
    print("  [INTEGRITY] Starting gap detection scan...")
    gaps = engine.detect_integrity_gaps()
    
    if not gaps:
        print("  [INTEGRITY] SUCCESS: Filesystem matches Event Ledger.")
    else:
        print(f"  [INTEGRITY] FOUND {len(gaps)} GAPS:")
        for gap in gaps:
            print(f"    - {gap}")

if __name__ == "__main__":
    main()
