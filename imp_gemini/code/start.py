# Implements: REQ-F-BOOT-002
import sys
from imp_gemini.code.internal.state_machine import StateManager, ProjectState

def main():
    state_mgr = StateManager()
    current_state = state_mgr.get_current_state()
    
    print(f"Detected State: {current_state.value}")
    
    if current_state == ProjectState.UNINITIALISED:
        print("Starting Progressive Init...")
        # Delegating to init logic (future iteration)
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
        print("Recommended Action: Spawn a discovery vector or request human review.")
    elif current_state == ProjectState.ALL_CONVERGED:
        print("Project ALL_CONVERGED. 🎉")
        print("Recommended Action: Run gen_status --gantt then gen_release.")
    else:
        print(f"Next step for {current_state.value} not yet implemented.")

if __name__ == "__main__":
    main()
