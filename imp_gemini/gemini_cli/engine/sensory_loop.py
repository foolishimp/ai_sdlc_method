import argparse
import sys
from pathlib import Path
from gemini_cli.engine.sensory import SensoryService

def main():
    parser = argparse.ArgumentParser(description="Background Sensory Service Loop")
    parser.add_argument("--workspace", required=True, help="Path to .ai-workspace")
    parser.add_argument("--interval", type=int, default=60, help="Scan interval in seconds")
    
    args = parser.parse_args()
    
    workspace_path = Path(args.workspace)
    if not workspace_path.exists():
        print(f"Error: Workspace path {workspace_path} does not exist.")
        sys.exit(1)
        
    service = SensoryService(workspace_path)
    service.run_continuous_loop(interval=args.interval)

if __name__ == "__main__":
    main()
