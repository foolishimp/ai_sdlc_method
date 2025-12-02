# AISDLC Plugin SDK Tests

Automated tests for the AI SDLC methodology plugin using Claude Code headless mode and the Claude Agent SDK.

## Quick Start

### Option 1: Shell Script (No dependencies)

```bash
# Run all tests
./test_headless.sh

# Run specific test suite
./test_headless.sh requirements
./test_headless.sh tdd
./test_headless.sh traceability
```

### Option 2: Pytest with SDK

```bash
# Install dependencies
pip install -r requirements.txt

# Run SDK tests
pytest test_aisdlc_sdk.py -v

# Run headless CLI tests
pytest test_headless_cli.py -v

# Run all tests
pytest . -v
```

## Test Structure

```
sdk/
├── conftest.py           # Pytest fixtures
├── test_aisdlc_sdk.py    # Claude Agent SDK tests
├── test_headless_cli.py  # Headless CLI tests
├── test_headless.sh      # Quick shell script tests
├── requirements.txt      # Python dependencies
└── README.md             # This file
```

## Test Categories

### SDK Tests (`test_aisdlc_sdk.py`)
- Uses `claude-agent-sdk` Python package
- Async tests with `pytest-asyncio`
- Full programmatic control

### CLI Tests (`test_headless_cli.py`)
- Uses `claude -p` headless mode
- Parses JSON output
- Good for CI/CD integration

### Shell Tests (`test_headless.sh`)
- Zero dependencies (just Claude CLI)
- Quick smoke tests
- Human-readable output

## CI/CD Integration

```yaml
# .github/workflows/test.yml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Claude CLI
        run: curl -fsSL https://claude.ai/install.sh | bash

      - name: Run quick tests
        run: .claude-plugin/tests/sdk/test_headless.sh basic

      - name: Install SDK
        run: pip install -r .claude-plugin/tests/sdk/requirements.txt

      - name: Run SDK tests
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: pytest .claude-plugin/tests/sdk/ -v --timeout=300
```

## Key Flags for Headless Mode

| Flag | Purpose |
|------|---------|
| `-p` | Non-interactive (print) mode |
| `--output-format json` | Structured output |
| `--max-turns N` | Limit conversation turns |
| `--allowedTools "Read,Write"` | Restrict tool access |
| `--resume SESSION_ID` | Continue previous session |

## Expected Outputs

### Requirements Stage
- Should generate `REQ-F-*` (functional) keys
- Should generate `REQ-NFR-*` (non-functional) keys
- Keys should follow format: `REQ-{TYPE}-{DOMAIN}-{NUMBER}`

### TDD Workflow
- Should mention RED phase (failing test)
- Should mention GREEN phase (implementation)
- Should mention REFACTOR phase

### Traceability
- REQ keys should propagate through stages
- Design should reference requirement keys
- Code should include `# Implements: REQ-*` comments
