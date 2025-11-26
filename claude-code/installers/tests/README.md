# Installer Tests

Tests for Claude Code installer utilities.

## Test Coverage

### test_setup_settings.py (24 tests)

**Validates**: REQ-F-PLUGIN-001, REQ-F-PLUGIN-002, REQ-F-PLUGIN-003

| Test Case | Description | Requirement |
|-----------|-------------|-------------|
| TC-SET-001 | Default initialization | REQ-F-PLUGIN-001 |
| TC-SET-002 | Initialization with all plugins | REQ-F-PLUGIN-001 |
| TC-SET-003 | Initialization with custom plugin list | REQ-F-PLUGIN-001 |
| TC-SET-004 | Initialization with directory source | REQ-F-PLUGIN-002 |
| TC-SET-005 | GitHub source configuration | REQ-F-PLUGIN-002 |
| TC-SET-006 | Directory source configuration | REQ-F-PLUGIN-002 |
| TC-SET-007 | Git URL source configuration | REQ-F-PLUGIN-002 |
| TC-SET-008 | Git source without URL returns None | REQ-F-PLUGIN-002 |
| TC-SET-009 | Plugin naming with GitHub source | REQ-F-PLUGIN-001 |
| TC-SET-010 | Plugin naming with directory source | REQ-F-PLUGIN-001 |
| TC-SET-011 | Merge into empty settings | REQ-F-PLUGIN-001 |
| TC-SET-012 | Preserve existing non-AISDLC settings | REQ-F-PLUGIN-001 |
| TC-SET-013 | Create new settings.json | REQ-F-PLUGIN-001 |
| TC-SET-014 | Dry run doesn't create file | REQ-F-PLUGIN-001 |
| TC-SET-015 | Backup created when overwriting | REQ-F-PLUGIN-001 |
| TC-SET-016 | Startup bundle contains correct plugins | REQ-F-PLUGIN-003 |
| TC-SET-017 | Enterprise bundle contains all plugins | REQ-F-PLUGIN-003 |
| TC-SET-018 | All bundles are defined | REQ-F-PLUGIN-003 |
| TC-SET-019 | Handle invalid JSON in existing settings | REQ-F-PLUGIN-001 |
| TC-SET-020 | Handle nonexistent target directory | REQ-F-PLUGIN-001 |
| TC-SET-021 | Existing AISDLC config without force flag | REQ-F-PLUGIN-001 |
| TC-SET-022 | Existing AISDLC config with force removes old | REQ-F-PLUGIN-001 |
| TC-SET-023 | ALL_PLUGINS contains expected count | REQ-F-PLUGIN-001 |
| TC-SET-024 | ALL_PLUGINS contains expected plugins | REQ-F-PLUGIN-001 |

## Running Tests

```bash
# Run all tests
cd claude-code/installers
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ -v --cov=. --cov-report=term-missing

# Run specific test class
python -m pytest tests/test_setup_settings.py::TestSettingsSetupInit -v
```

## Requirement Traceability

| Requirement | Description | Coverage |
|-------------|-------------|----------|
| REQ-F-PLUGIN-001 | Plugin system with marketplace support | 18 tests |
| REQ-F-PLUGIN-002 | Federated plugin loading (github, directory, git) | 5 tests |
| REQ-F-PLUGIN-003 | Plugin bundles | 3 tests |

## Test Classes

1. **TestSettingsSetupInit** - Initialization and configuration
2. **TestBuildMarketplaceConfig** - Marketplace source configuration
3. **TestBuildPluginsConfig** - Plugin naming and enablement
4. **TestMergeSettings** - Settings merging and preservation
5. **TestWriteSettings** - File creation and backup
6. **TestPluginBundles** - Bundle definitions
7. **TestEdgeCases** - Error handling and edge cases
8. **TestAllPlugins** - ALL_PLUGINS constant validation
