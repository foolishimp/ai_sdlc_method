# Implements: REQ-F-BOOT-002
import sys
from imp_gemini.code.internal.state_machine import StateManager, ProjectState

def main():
    state_mgr = StateManager()
    current_state = state_mgr.get_current_state()
    
    print(f"Detected State: {current_state.value}")
    
    if current_state == ProjectState.UNINITIALISED:
        print("Project UNINITIALISED.")
        print("Recommended Action: Run /gen-init to scaffold the workspace.")
    elif current_state == ProjectState.NEEDS_CONSTRAINTS:
        print("Project NEEDS_CONSTRAINTS.")
        print("Recommended Action: Configure .ai-workspace/gemini_genesis/project_constraints.yml")
    elif current_state == ProjectState.NEEDS_INTENT:
        print("Project NEEDS_INTENT.")
        print("Recommended Action: Define your goal in .ai-workspace/spec/INTENT.md")
    elif current_state == ProjectState.NO_FEATURES:
        print("Project has NO_FEATURES.")
        print("Recommended Action: Run /gen-spawn --type feature to start a new feature vector.")
    elif current_state == ProjectState.IN_PROGRESS:
        feature = state_mgr.get_next_actionable_feature()
        if feature:
            edge = state_mgr.get_next_edge(feature)
            print(f"Feature: {feature.get('feature')} \"{feature.get('title')}\"")
            print(f"Next Edge: {edge}")
            print(f"Delegating to /gen-iterate --edge \"{edge}\" --feature \"{feature.get('feature')}\"")
        else:
            print("No actionable features found in IN_PROGRESS state.")
    elif current_state == ProjectState.STUCK:
        print("ALERT: Project is STUCK. Iteration delta is unchanged.")
        print("Recommended Action: Run /gen-escalate to human or spawn a discovery vector.")
    elif current_state == ProjectState.ALL_CONVERGED:
        print("Project ALL_CONVERGED. 🎉")
        print("Recommended Action: Run /gen-status --gantt then /gen-release.")
    elif current_state == ProjectState.ALL_BLOCKED:
        print("Project ALL_BLOCKED. ✗")
        print("Recommended Action: Check dependencies in feature vector files.")
    else:
        print(f"Next step for {current_state.value} not yet implemented.")

if __name__ == "__main__":
    main()
