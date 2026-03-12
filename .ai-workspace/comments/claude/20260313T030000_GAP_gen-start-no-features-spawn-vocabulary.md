# GAP: gen-start NO_FEATURES path — gen-spawn vocabulary mismatch

**Author**: claude
**Date**: 2026-03-13T03:00:00+11:00
**Observed during**: genesis_manager first boot, `/gen-start --auto`
**For**: all

## Observation

When `gen-start` detects `NO_FEATURES` state, its Step 4 delegates to:

```
/gen-spawn --type feature
```

But `gen-spawn` was designed exclusively for **child vectors** — discovery, spike, poc, hotfix — spawned from an existing parent feature. It has no vocabulary for `--type feature` and no concept of a root (parentless) feature vector.

The system caught this mismatch at runtime and self-corrected, handling root feature creation directly. The fallback worked, but it is undocumented and fragile.

## The Gap

`gen-start` Step 4 says:

> "Inform the user: 'Intent captured. Let's create your first feature vector.' Delegate to `/gen-spawn --type feature`."

This delegation is incorrect. `gen-spawn` is a child-vector spawner. A root feature vector has:
- no `parent.feature`
- no `parent.edge`
- no `time_box` (by default)
- no fold-back destination

These are structurally different from what `gen-spawn` produces.

## Options

### Option A: Add `--type feature` to gen-spawn
Extend gen-spawn to accept `--type feature` with `--parent` optional. When `--parent` is absent, create a root feature vector with standard profile and no time-box. This is the smallest change.

### Option B: Add a dedicated root feature scaffolding step to gen-start
`gen-start` Step 4 handles root feature creation directly — reads INTENT.md, derives a feature title and ID, creates the `.yml` from the feature_vector_template, and emits a `spawn_created` event. `gen-spawn` remains child-vector only.

### Option C: Rename gen-spawn to gen-spawn-child, add gen-spawn as the unified command
`gen-spawn` becomes the general-purpose vector creator: `--type feature|discovery|spike|poc|hotfix`. When `--type feature` and no `--parent`, it creates a root vector. Other types require `--parent`.

## Recommended Fix

**Option A** is the smallest correct fix. The command name `gen-spawn` is appropriate for root feature creation too — you are spawning a new vector into existence. Add `--parent` as optional, and when absent, create a root feature vector using the `standard` profile with no time-box, no fold-back.

The spec change is minimal:
- `gen-spawn` gains `--type feature` in its vocabulary
- `--parent` becomes optional (required only for discovery/spike/poc/hotfix)
- Root feature vectors get `vector_type: feature`, `profile: standard`, `parent: null`

## Severity

Low — the fallback works correctly. This is a spec precision gap, not a runtime failure. The system self-corrects by handling root feature creation inline in `gen-start` when `gen-spawn` does not recognise the type.

The gap should be closed before the next time someone reads `gen-start` Step 4 and expects `gen-spawn --type feature` to work as documented.
