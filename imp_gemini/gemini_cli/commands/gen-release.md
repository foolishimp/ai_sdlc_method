# gen release
**Implements**: REQ-TOOL-004, REQ-LIFE-001

## Usage
`gen release --version <SEMVER>`

## Description
Generates a release manifest summarizing the converged feature vectors (REQ keys) for a specific version.

## Effects
- Collects all REQ keys from converged feature vectors.
- Generates a `release_manifest.json` in `.ai-workspace/snapshots/`.
- Emits a `release_manifest_generated` event.
