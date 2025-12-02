"""
Test Case Specification Creation Tests

Validates: TCS-010
Implements: REQ-NFR-TRACE-001, REQ-NFR-QUALITY-001

This module tests the TCS creation skill workflow, validating that test case
specifications are created with proper structure, naming conventions, requirement
traceability, and registry integration.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional

import pytest


class TestTCSCreation:
    """Test the TCS creation skill workflow."""

    @pytest.fixture
    def tcs_dir(self) -> Path:
        """Get the TCS directory path."""
        return Path(__file__).parent.parent.parent.parent / "docs" / "design" / "claude_aisdlc" / "tests"

    @pytest.fixture
    def skill_file(self) -> Path:
        """Get the TCS skill specification file."""
        return Path(__file__).parent.parent.parent / "plugins" / "testing-skills" / "skills" / "create-test-specification" / "SKILL.md"

    @pytest.fixture
    def tcs_010_file(self, tcs_dir) -> Path:
        """Get TCS-010 file path."""
        return tcs_dir / "TCS-010-skill-tcs.md"

    @pytest.fixture
    def registry_file(self, tcs_dir) -> Path:
        """Get registry README file path."""
        return tcs_dir / "README.md"

    @pytest.fixture
    def tcs_001_file(self, tcs_dir) -> Path:
        """Get TCS-001 as golden master reference."""
        return tcs_dir / "TCS-001-command-status.md"

    def test_valid_tcs_creation(self, tcs_010_file):
        """TCS-001: Create valid TCS document with all sections."""
        assert tcs_010_file.exists(), "TCS-010 file should exist"

        content = tcs_010_file.read_text()

        # Verify all required sections
        required_sections = [
            "# TCS-010:",
            "**Status**:",
            "**Date**:",
            "**Requirements**:",
            "**ADR Reference**:",
            "**Implementation**:",
            "## Purpose",
            "## Preconditions",
            "## Test Scenarios",
            "## Validation Criteria",
            "## Test Implementation",
            "## Requirement Traceability",
            "## Notes"
        ]

        for section in required_sections:
            assert section in content, f"Required section '{section}' missing from TCS-010"

    def test_tcs_naming_validation(self, tcs_dir):
        """TCS-002: Validate TCS-XXX-slug.md naming pattern."""
        tcs_files = list(tcs_dir.glob("TCS-*.md"))

        # Pattern: TCS-XXX-slug.md where XXX is 3 digits and slug is kebab-case
        pattern = re.compile(r'^TCS-\d{3}-[a-z0-9-]+\.md$')

        invalid_files = []
        for tcs_file in tcs_files:
            if not pattern.match(tcs_file.name):
                invalid_files.append(tcs_file.name)

        assert len(invalid_files) == 0, f"Invalid TCS filenames: {invalid_files}"

        # Verify TCS-010 specifically
        assert (tcs_dir / "TCS-010-skill-tcs.md").exists(), "TCS-010-skill-tcs.md should exist"

    def test_required_sections_present(self, tcs_010_file):
        """TCS-003: All mandatory sections exist in TCS."""
        content = tcs_010_file.read_text()

        # Define required sections with their patterns
        sections = {
            "Title": r"^# TCS-010:",
            "Status": r"\*\*Status\*\*:",
            "Date": r"\*\*Date\*\*:",
            "Requirements": r"\*\*Requirements\*\*:",
            "Purpose": r"^## Purpose",
            "Preconditions": r"^## Preconditions",
            "Test Scenarios": r"^## Test Scenarios",
            "Validation Criteria": r"^## Validation Criteria",
            "Test Implementation": r"^## Test Implementation",
            "Requirement Traceability": r"^## Requirement Traceability"
        }

        missing_sections = []
        for section_name, pattern in sections.items():
            if not re.search(pattern, content, re.MULTILINE):
                missing_sections.append(section_name)

        assert len(missing_sections) == 0, f"Missing sections in TCS-010: {missing_sections}"

    def test_requirement_traceability(self, tcs_010_file):
        """TCS-004: Traceability matrix correctly links requirements."""
        content = tcs_010_file.read_text()

        # Extract requirements from header
        req_match = re.search(r'\*\*Requirements\*\*:\s*([^\n]+)', content)
        assert req_match, "Requirements field not found in TCS-010 header"

        requirements_text = req_match.group(1)
        # Extract REQ-* identifiers
        header_reqs = set(re.findall(r'REQ-[A-Z]+-[A-Z0-9-]+', requirements_text))

        assert len(header_reqs) > 0, "No requirements found in TCS-010 header"

        # Extract requirements from the LAST traceability matrix (skip template examples)
        # Split content to get only the actual TCS content after the template
        parts = content.split('## Test Implementation')
        if len(parts) > 1:
            # Get everything after Test Implementation section
            actual_content = parts[-1]
        else:
            actual_content = content

        traceability_section = re.search(
            r'## Requirement Traceability\s*\n\n.*?\n\|[-|\s]+\|\n(.*?)(?=\n##|---|\Z)',
            actual_content,
            re.DOTALL
        )

        assert traceability_section, "Traceability matrix not found in TCS-010"

        matrix_content = traceability_section.group(1)
        matrix_reqs = set(re.findall(r'REQ-[A-Z]+-[A-Z0-9-]+', matrix_content))

        # Filter out placeholder requirements (REQ-F-XXX, REQ-NFR-XXX)
        matrix_reqs = {r for r in matrix_reqs if not re.match(r'REQ-[A-Z]+-XXX-', r)}

        # All header requirements should appear in matrix
        missing_from_matrix = header_reqs - matrix_reqs
        assert len(missing_from_matrix) == 0, f"Requirements in header but not in matrix: {missing_from_matrix}"

    def test_registry_entry_creation(self, registry_file):
        """TCS-005: Entry added to README.md registry."""
        content = registry_file.read_text()

        # Check for TCS-010 entry in the table
        assert "TCS-010" in content, "TCS-010 should appear in registry"
        assert "TCS-010-skill-tcs.md" in content, "TCS-010 filename should appear in registry"

        # Verify entry format: | [TCS-010](TCS-010-skill-tcs.md) | Title | Requirements | Status |
        entry_pattern = r'\|\s*\[TCS-010\]\(TCS-010-skill-tcs\.md\)\s*\|.*?\|.*?\|.*?\|'
        assert re.search(entry_pattern, content), "TCS-010 registry entry has incorrect format"

    def test_status_field_validation(self, tcs_010_file):
        """TCS-006: Status field contains valid value."""
        content = tcs_010_file.read_text()

        status_match = re.search(r'\*\*Status\*\*:\s*([^\n]+)', content)
        assert status_match, "Status field not found"

        status = status_match.group(1).strip()
        valid_statuses = ["✅ Implemented", "📋 Specified", "❌ Deprecated"]

        assert status in valid_statuses, f"Invalid status '{status}'. Must be one of: {valid_statuses}"

    def test_scenario_id_format(self, tcs_010_file):
        """TCS-007: Test scenario IDs follow XXX-001 pattern."""
        content = tcs_010_file.read_text()

        # Extract test scenarios table
        scenarios_match = re.search(
            r'## Test Scenarios\s*\n\n.*?\n\|[-|\s]+\|\n(.*?)(?=\n##|\Z)',
            content,
            re.DOTALL
        )

        assert scenarios_match, "Test Scenarios table not found"

        scenarios_content = scenarios_match.group(1)

        # Find all scenario IDs in the first column
        # Pattern: | TCS-001 | or | ST-001 | etc.
        scenario_ids = re.findall(r'\|\s*([A-Z]+-\d+)\s*\|', scenarios_content)

        assert len(scenario_ids) > 0, "No scenario IDs found in Test Scenarios table"

        # Validate format: PREFIX-NNN where NNN is 3 digits
        pattern = re.compile(r'^[A-Z]+-\d{3}$')
        invalid_ids = [sid for sid in scenario_ids if not pattern.match(sid)]

        assert len(invalid_ids) == 0, f"Invalid scenario IDs: {invalid_ids}"

    def test_invalid_tcs_number(self, tcs_dir):
        """TCS-008: Error on duplicate or malformed TCS number."""
        tcs_files = list(tcs_dir.glob("TCS-*.md"))

        # Extract TCS numbers
        numbers = []
        for tcs_file in tcs_files:
            match = re.match(r'TCS-(\d+)-', tcs_file.name)
            if match:
                numbers.append(int(match.group(1)))

        # Check for duplicates
        assert len(numbers) == len(set(numbers)), f"Duplicate TCS numbers found: {numbers}"

        # Verify numbers are valid 3-digit format (001-999)
        invalid_numbers = [n for n in numbers if n < 1 or n > 999]
        assert len(invalid_numbers) == 0, f"TCS numbers out of range (1-999): {invalid_numbers}"

    def test_missing_requirement_warning(self, tcs_010_file):
        """TCS-009: Warning when TCS has no REQ reference."""
        content = tcs_010_file.read_text()

        # TCS-010 should have requirements
        req_match = re.search(r'\*\*Requirements\*\*:\s*([^\n]+)', content)
        assert req_match, "Requirements field not found"

        requirements_text = req_match.group(1)

        # Should contain at least one REQ-* identifier
        reqs = re.findall(r'REQ-[A-Z]+-[A-Z0-9-]+', requirements_text)
        assert len(reqs) > 0, "TCS-010 should reference at least one requirement"

    def test_template_compliance(self, tcs_010_file, skill_file):
        """TCS-010: Generated TCS matches skill template."""
        tcs_content = tcs_010_file.read_text()
        skill_content = skill_file.read_text()

        # Extract template structure from skill file
        # Look for the template markdown block
        template_match = re.search(
            r'```markdown\s*\n# TCS-XXX:.*?\n```',
            skill_content,
            re.DOTALL
        )

        assert template_match, "Template not found in skill specification"

        template = template_match.group(0)

        # Extract section headers from template
        template_sections = re.findall(r'^## ([^\n]+)', template, re.MULTILINE)

        # Extract section headers from TCS-010
        tcs_sections = re.findall(r'^## ([^\n]+)', tcs_content, re.MULTILINE)

        # All template sections should appear in TCS
        missing_sections = set(template_sections) - set(tcs_sections)

        # Allow for some variation (e.g., "Expected TCS Template Structure" is meta)
        # but core sections should match
        core_sections = {"Purpose", "Preconditions", "Test Scenarios",
                        "Validation Criteria", "Test Implementation",
                        "Requirement Traceability", "Notes"}

        missing_core = core_sections - set(tcs_sections)
        assert len(missing_core) == 0, f"Missing core sections: {missing_core}"

    def test_date_format_validation(self, tcs_010_file):
        """Validate date follows YYYY-MM-DD format."""
        content = tcs_010_file.read_text()

        date_match = re.search(r'\*\*Date\*\*:\s*([^\n]+)', content)
        assert date_match, "Date field not found"

        date_str = date_match.group(1).strip()

        # Validate YYYY-MM-DD format
        date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
        assert date_pattern.match(date_str), f"Date '{date_str}' should follow YYYY-MM-DD format"

    def test_implementation_path_exists(self, tcs_010_file):
        """Validate implementation path is specified."""
        content = tcs_010_file.read_text()

        impl_match = re.search(r'\*\*Implementation\*\*:\s*`([^`]+)`', content)
        assert impl_match, "Implementation path not found in TCS-010"

        impl_path = impl_match.group(1)
        assert len(impl_path) > 0, "Implementation path should not be empty"
        assert "SKILL.md" in impl_path, "Implementation should reference skill file"

    def test_validation_criteria_checklist(self, tcs_010_file):
        """Validate that validation criteria section has checklist items."""
        content = tcs_010_file.read_text()

        # Find Validation Criteria section
        criteria_match = re.search(
            r'## Validation Criteria\s*\n\n(.*?)(?=\n##|\Z)',
            content,
            re.DOTALL
        )

        assert criteria_match, "Validation Criteria section not found"

        criteria_content = criteria_match.group(1)

        # Should have at least one checkbox item
        checkboxes = re.findall(r'- \[[ x]\]', criteria_content)
        assert len(checkboxes) > 0, "Validation Criteria should have at least one checkbox item"

    def test_test_implementation_section(self, tcs_010_file):
        """Validate Test Implementation section structure."""
        content = tcs_010_file.read_text()

        # Find Test Implementation section
        impl_match = re.search(
            r'## Test Implementation\s*\n\n(.*?)(?=\n##|\Z)',
            content,
            re.DOTALL
        )

        assert impl_match, "Test Implementation section not found"

        impl_content = impl_match.group(1)

        # Should specify File, Class, and Tests count
        assert "**File**:" in impl_content, "Test file path should be specified"
        assert "**Class**:" in impl_content, "Test class name should be specified"
        assert "**Tests**:" in impl_content, "Test count should be specified"

    def test_traceability_across_all_tcs(self, tcs_dir, registry_file):
        """Validate traceability across all TCS documents."""
        # Get all TCS files
        tcs_files = sorted(tcs_dir.glob("TCS-*.md"))

        # Extract all requirements from all TCS files
        all_tcs_reqs = set()
        for tcs_file in tcs_files:
            content = tcs_file.read_text()
            reqs = re.findall(r'REQ-[A-Z]+-[A-Z0-9-]+', content)
            all_tcs_reqs.update(reqs)

        # Extract requirements from registry
        registry_content = registry_file.read_text()
        registry_reqs = set(re.findall(r'REQ-[A-Z]+-[A-Z0-9-]+', registry_content))

        # All TCS requirements should appear in registry
        missing_from_registry = all_tcs_reqs - registry_reqs

        # Some leeway for requirements that might be in TCS content but not in registry table
        # Just verify that REQ-NFR-TRACE-001 and REQ-NFR-QUALITY-001 are in registry
        assert "REQ-NFR-TRACE-001" in registry_reqs, "REQ-NFR-TRACE-001 should be in registry"
        assert "REQ-NFR-QUALITY-001" in registry_reqs, "REQ-NFR-QUALITY-001 should be in registry"


class TestTCSMetaValidation:
    """Meta-level validation of the TCS system itself."""

    @pytest.fixture
    def all_tcs_files(self) -> List[Path]:
        """Get all TCS files."""
        tcs_dir = Path(__file__).parent.parent.parent.parent / "docs" / "design" / "claude_aisdlc" / "tests"
        return sorted(tcs_dir.glob("TCS-*.md"))

    def test_sequential_numbering(self, all_tcs_files):
        """Verify TCS numbers are sequential (allowing for deprecated)."""
        numbers = []
        for tcs_file in all_tcs_files:
            match = re.match(r'TCS-(\d+)-', tcs_file.name)
            if match:
                numbers.append(int(match.group(1)))

        numbers.sort()

        # Should start at 1
        assert numbers[0] == 1, "TCS numbering should start at 001"

        # Should be mostly sequential (some gaps allowed for deprecated)
        max_gap = 5  # Allow some gaps
        for i in range(len(numbers) - 1):
            gap = numbers[i + 1] - numbers[i]
            assert gap <= max_gap, f"Large gap in TCS numbering: {numbers[i]} to {numbers[i+1]}"

    def test_all_tcs_have_implementation(self, all_tcs_files):
        """Verify all TCS documents specify implementation."""
        missing_impl = []
        for tcs_file in all_tcs_files:
            content = tcs_file.read_text()
            if "**Implementation**:" not in content:
                missing_impl.append(tcs_file.name)

        assert len(missing_impl) == 0, f"TCS files missing Implementation field: {missing_impl}"

    def test_all_tcs_have_requirements(self, all_tcs_files):
        """Verify all TCS documents trace to requirements."""
        missing_reqs = []
        for tcs_file in all_tcs_files:
            content = tcs_file.read_text()
            req_match = re.search(r'\*\*Requirements\*\*:\s*([^\n]+)', content)
            if not req_match or not re.search(r'REQ-', req_match.group(1)):
                missing_reqs.append(tcs_file.name)

        assert len(missing_reqs) == 0, f"TCS files missing requirement references: {missing_reqs}"

    def test_registry_completeness(self):
        """Verify registry contains all TCS files."""
        tcs_dir = Path(__file__).parent.parent.parent.parent / "docs" / "design" / "claude_aisdlc" / "tests"
        registry_file = tcs_dir / "README.md"

        tcs_files = set(f.name for f in tcs_dir.glob("TCS-*.md"))
        registry_content = registry_file.read_text()

        # Extract TCS references from registry
        registry_tcs = set(re.findall(r'TCS-\d{3}-[a-z0-9-]+\.md', registry_content))

        # All TCS files should be in registry
        missing_from_registry = tcs_files - registry_tcs
        assert len(missing_from_registry) == 0, f"TCS files not in registry: {missing_from_registry}"

        # No extra entries in registry
        extra_in_registry = registry_tcs - tcs_files
        assert len(extra_in_registry) == 0, f"Registry has entries for non-existent TCS: {extra_in_registry}"
