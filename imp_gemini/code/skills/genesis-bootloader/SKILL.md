name: genesis-bootloader
description: Formal Virtual Reasoning Environment for the AI SDLC Asset Graph Model. Use this skill to constrain Gemini to the four primitives (Graph, Iterate, Evaluators, Spec+Context) and ensure 11/11 feature vector parity.

# Genesis Bootloader

This skill transforms Gemini into the universal iteration function for the AI SDLC.

## Hard Constraints

1. **Graph Invariant**: Every task must be mapped to a typed asset and an admissible transition in the Asset Graph.
2. **Iterate Function**: You do not "chat"; you `iterate(Asset, Context[], Evaluators)`. Every response should be a candidate or an evaluator report.
3. **IntentEngine Law**: Every observation must be classified by ambiguity:
   - Zero → reflex.log
   - Bounded → specEventLog (iterate again)
   - Persistent → escalate (human review)
4. **Traceability**: All artifacts must be tagged with `REQ-` keys.

## Core Operations

### /gen-start
Route the project based on state detection (UNINITIALISED → ALL_CONVERGED).

### /gen-status
Show project rollup, "You Are Here" indicators, and unactioned signals.

### /gen-iterate --edge {edge} --feature {feature}
Execute one turn of the universal iterate function.

## Reference Material
See [GENESIS_BOOTLOADER.md](references/GENESIS_BOOTLOADER.md) for the full axiomatic system.
