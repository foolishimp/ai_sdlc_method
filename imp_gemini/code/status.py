# Implements: REQ-F-BOOT-003
from imp_gemini.code.internal.state_machine import StateManager

def main():
    state_mgr = StateManager()
    current_state = state_mgr.get_current_state()
    
    print("AI SDLC Status — gemini-genesis")
    print("=" * 30)
    print(f"State: {current_state.value}")
    
    print("\nYou Are Here:")
    features = state_mgr.get_active_features()
    if not features:
        print("  No active features.")
    else:
        for feat in features:
            fid = feat.get("feature", "UNKNOWN")
            traj = feat.get("trajectory", {})
            
            def get_marker(phase):
                p_status = traj.get(phase, {}).get("status", "pending")
                if p_status == "converged": return "✓"
                if p_status == "iterating": return "●"
                return "○"

            req = get_marker("requirements")
            des = get_marker("design")
            cod = get_marker("code")
            tst = get_marker("unit_tests")
            
            print(f"  {fid:<15} intent ✓ → req {req} → design {des} → code {cod} → tests {tst}")

if __name__ == "__main__":
    main()
