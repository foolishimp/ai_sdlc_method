import time
import sys
from pathlib import Path

# Add imp_gemini to sys.path
sys.path.append(str(Path.cwd() / "imp_gemini"))

from gemini_cli.engine.otlp_relay import OTLPRelay

def main():
    workspace_root = Path.cwd() / "imp_gemini" / ".ai-workspace"
    relay = OTLPRelay(workspace_root)
    relay.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        relay.stop()
        print("\n  [OTLP] Relay stopped.")

if __name__ == "__main__":
    main()
