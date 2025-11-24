#!/usr/bin/env python3
"""
Traceability Validation Tool

Validates requirement traceability across the AI SDLC lifecycle:
- Requirements (REQ-*) → Design → Code → Tests

# Implements: REQ-NFR-TRACE-001 (Full Lifecycle Traceability)
# Implements: REQ-NFR-TRACE-002 (Requirement Key Propagation)

Usage:
    python validate_traceability.py --check-all
    python validate_traceability.py --requirements docs/requirements/
    python validate_traceability.py --design docs/design/
    python validate_traceability.py --code installers/ mcp_service/ plugins/
    python validate_traceability.py --matrix > docs/TRACEABILITY_MATRIX.md
    python validate_traceability.py --inventory > INVENTORY.md
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict


class TraceabilityValidator:
    """Validates requirement traceability across SDLC stages."""

    # Requirement key patterns
    REQ_PATTERN = re.compile(r'(REQ-[A-Z]+-[A-Z0-9]+-\d{3})')

    # Traceability tag patterns
    IMPLEMENTS_PATTERN = re.compile(r'#\s*Implements:\s*(REQ-[A-Z]+-[A-Z0-9]+-\d{3})', re.IGNORECASE)
    VALIDATES_PATTERN = re.compile(r'#\s*Validates:\s*(REQ-[A-Z]+-[A-Z0-9]+-\d{3})', re.IGNORECASE)
    ARROW_PATTERN = re.compile(r'→\s*(REQ-[A-Z]+-[A-Z0-9]+-\d{3})')

    def __init__(self):
        self.requirements: Dict[str, dict] = {}  # REQ-ID → {file, line, description}
        self.design_refs: Dict[str, List[Tuple[str, int]]] = defaultdict(list)  # REQ-ID → [(file, line)]
        self.code_refs: Dict[str, List[Tuple[str, int]]] = defaultdict(list)  # REQ-ID → [(file, line)]
        self.test_refs: Dict[str, List[Tuple[str, int]]] = defaultdict(list)  # REQ-ID → [(file, line)]

    def extract_requirements(self, requirements_dir: Path) -> None:
        """Extract all requirement keys from requirements documents.

        Only scans *.md files directly in requirements_dir, not subdirectories.
        This excludes examples/ subdirectory with documentation-only requirements.
        """
        print(f"📋 Scanning requirements in: {requirements_dir}")

        requirements_dir = requirements_dir.resolve()
        cwd = Path.cwd().resolve()

        for md_file in requirements_dir.glob("*.md"):
            with open(md_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, 1):
                matches = self.REQ_PATTERN.findall(line)
                for req_id in matches:
                    if req_id not in self.requirements:
                        # Extract description (rest of line after REQ-ID)
                        desc = line.split(req_id, 1)[1].strip()
                        try:
                            rel_path = str(md_file.relative_to(cwd))
                        except ValueError:
                            rel_path = str(md_file)
                        self.requirements[req_id] = {
                            'file': rel_path,
                            'line': line_num,
                            'description': desc[:80]  # Truncate long descriptions
                        }

        print(f"   Found {len(self.requirements)} requirement keys\n")

    def scan_design_docs(self, design_dir: Path) -> None:
        """Scan design documents for requirement traceability tags."""
        print(f"🎨 Scanning design documents in: {design_dir}")

        design_dir = design_dir.resolve()
        cwd = Path.cwd().resolve()

        for md_file in design_dir.glob("**/*.md"):
            with open(md_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            try:
                rel_path = str(md_file.relative_to(cwd))
            except ValueError:
                rel_path = str(md_file)

            for line_num, line in enumerate(lines, 1):
                # Look for → REQ-* pattern
                for match in self.ARROW_PATTERN.finditer(line):
                    req_id = match.group(1)
                    self.design_refs[req_id].append((rel_path, line_num))

                # Look for explicit REQ-* mentions
                for match in self.REQ_PATTERN.finditer(line):
                    req_id = match.group(1)
                    if req_id not in [ref[0] for ref in self.design_refs[req_id]]:
                        self.design_refs[req_id].append((rel_path, line_num))

        total_refs = sum(len(refs) for refs in self.design_refs.values())
        print(f"   Found {total_refs} design references to {len(self.design_refs)} requirements\n")

    def scan_code(self, code_dirs: List[Path]) -> None:
        """Scan code for requirement traceability tags."""
        print(f"💻 Scanning code in: {', '.join(str(d) for d in code_dirs)}")

        cwd = Path.cwd().resolve()

        for code_dir in code_dirs:
            code_dir = code_dir.resolve()
            if not code_dir.exists():
                print(f"   ⚠️  Directory not found: {code_dir}")
                continue

            for py_file in code_dir.glob("**/*.py"):
                with open(py_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                try:
                    rel_path = str(py_file.relative_to(cwd))
                except ValueError:
                    rel_path = str(py_file)

                for line_num, line in enumerate(lines, 1):
                    # Look for # Implements: REQ-*
                    for match in self.IMPLEMENTS_PATTERN.finditer(line):
                        req_id = match.group(1)
                        self.code_refs[req_id].append((rel_path, line_num))

                    # Look for # Validates: REQ-*
                    for match in self.VALIDATES_PATTERN.finditer(line):
                        req_id = match.group(1)
                        self.test_refs[req_id].append((rel_path, line_num))

        code_total = sum(len(refs) for refs in self.code_refs.values())
        test_total = sum(len(refs) for refs in self.test_refs.values())
        print(f"   Found {code_total} code implementations of {len(self.code_refs)} requirements")
        print(f"   Found {test_total} test validations of {len(self.test_refs)} requirements\n")

    def validate(self) -> Tuple[List[str], List[str], List[str]]:
        """
        Validate traceability.

        Returns:
            Tuple of (unimplemented_reqs, untested_reqs, orphaned_refs)
        """
        print("🔍 Validating traceability...\n")

        # Find requirements without implementation
        unimplemented = []
        for req_id in self.requirements:
            if req_id not in self.code_refs:
                unimplemented.append(req_id)

        # Find requirements without tests
        untested = []
        for req_id in self.requirements:
            if req_id not in self.test_refs:
                untested.append(req_id)

        # Find design/code references to non-existent requirements
        orphaned = []
        all_refs = set(self.design_refs.keys()) | set(self.code_refs.keys()) | set(self.test_refs.keys())
        for req_id in all_refs:
            if req_id not in self.requirements:
                orphaned.append(req_id)

        return unimplemented, untested, orphaned

    def generate_inventory(self) -> str:
        """Generate component inventory showing files implementing requirements."""
        output = []
        output.append("# Component Inventory (Auto-Generated)")
        output.append("")
        output.append("**Generated from**: Filesystem scan + requirement traceability")
        output.append("**Tool**: `python installers/validate_traceability.py --inventory`")
        output.append("**Last Updated**: Auto-generated on demand")
        output.append("")
        output.append("---")
        output.append("")
        output.append("## Summary")
        output.append("")
        output.append(f"- **Total Requirements**: {len(self.requirements)}")
        output.append(f"- **Components with Implementations**: {len(set(f for refs in self.code_refs.values() for f, _ in refs))}")
        output.append(f"- **Design Documents**: {len(set(f for refs in self.design_refs.values() for f, _ in refs))}")
        output.append(f"- **Test Files**: {len(set(f for refs in self.test_refs.values() for f, _ in refs))}")
        output.append("")

        # Coverage stats
        if self.requirements:
            design_coverage = (len(self.design_refs) / len(self.requirements)) * 100
            code_coverage = (len(self.code_refs) / len(self.requirements)) * 100
            test_coverage = (len(self.test_refs) / len(self.requirements)) * 100
            output.append(f"- **Design Coverage**: {design_coverage:.1f}%")
            output.append(f"- **Implementation Coverage**: {code_coverage:.1f}%")
            output.append(f"- **Test Coverage**: {test_coverage:.1f}%")
        output.append("")
        output.append("---")
        output.append("")

        # Component breakdown by requirement
        output.append("## Components by Requirement Category")
        output.append("")

        # Group requirements by type
        req_by_type = defaultdict(list)
        for req_id in self.requirements:
            req_type = req_id.split('-')[1] if '-' in req_id else 'UNKNOWN'
            req_by_type[req_type].append(req_id)

        for req_type in sorted(req_by_type.keys()):
            output.append(f"### {req_type} Requirements ({len(req_by_type[req_type])})")
            output.append("")

            implemented = sum(1 for req in req_by_type[req_type] if req in self.code_refs)
            tested = sum(1 for req in req_by_type[req_type] if req in self.test_refs)

            output.append(f"- **Total**: {len(req_by_type[req_type])}")
            output.append(f"- **Implemented**: {implemented}")
            output.append(f"- **Tested**: {tested}")
            output.append("")

            # List implementing files
            files_for_type = set()
            for req in req_by_type[req_type]:
                if req in self.code_refs:
                    files_for_type.update(f for f, _ in self.code_refs[req])

            if files_for_type:
                output.append("**Implementation Files**:")
                for file in sorted(files_for_type):
                    output.append(f"- {file}")
                output.append("")

        output.append("---")
        output.append("")
        output.append("## Note")
        output.append("")
        output.append("This inventory is **auto-generated** from code traceability tags.")
        output.append("For detailed requirement-to-artifact mapping, see `docs/TRACEABILITY_MATRIX.md`")
        output.append("")

        return "\n".join(output)

    def generate_matrix(self) -> str:
        """Generate traceability matrix in markdown format."""
        output = []
        output.append("# Requirements Traceability Matrix")
        output.append("")
        output.append("**Generated**: " + str(Path.cwd()))
        output.append("")
        output.append("## Summary")
        output.append("")
        output.append(f"- **Total Requirements**: {len(self.requirements)}")
        output.append(f"- **Requirements with Design**: {len(self.design_refs)}")
        output.append(f"- **Requirements with Implementation**: {len(self.code_refs)}")
        output.append(f"- **Requirements with Tests**: {len(self.test_refs)}")
        output.append("")

        # Calculate coverage
        if self.requirements:
            design_coverage = (len(self.design_refs) / len(self.requirements)) * 100
            code_coverage = (len(self.code_refs) / len(self.requirements)) * 100
            test_coverage = (len(self.test_refs) / len(self.requirements)) * 100

            output.append(f"- **Design Coverage**: {design_coverage:.1f}%")
            output.append(f"- **Implementation Coverage**: {code_coverage:.1f}%")
            output.append(f"- **Test Coverage**: {test_coverage:.1f}%")
        output.append("")
        output.append("---")
        output.append("")

        # Full traceability table
        output.append("## Full Traceability")
        output.append("")
        output.append("| Requirement | Description | Design | Implementation | Tests | Status |")
        output.append("|-------------|-------------|--------|----------------|-------|--------|")

        for req_id in sorted(self.requirements.keys()):
            req = self.requirements[req_id]
            desc = req['description'][:40]

            # Design references
            design = "✅" if req_id in self.design_refs else "❌"
            design_count = len(self.design_refs.get(req_id, []))
            if design_count > 0:
                design = f"✅ ({design_count})"

            # Code references
            code = "✅" if req_id in self.code_refs else "❌"
            code_count = len(self.code_refs.get(req_id, []))
            if code_count > 0:
                code = f"✅ ({code_count})"

            # Test references
            tests = "✅" if req_id in self.test_refs else "❌"
            test_count = len(self.test_refs.get(req_id, []))
            if test_count > 0:
                tests = f"✅ ({test_count})"

            # Overall status
            has_design = req_id in self.design_refs
            has_code = req_id in self.code_refs
            has_tests = req_id in self.test_refs

            if has_design and has_code and has_tests:
                status = "✅ Complete"
            elif has_code and has_tests:
                status = "⚠️ No Design"
            elif has_design and has_code:
                status = "⚠️ No Tests"
            elif has_design:
                status = "🚧 Design Only"
            else:
                status = "❌ Not Started"

            output.append(f"| {req_id} | {desc} | {design} | {code} | {tests} | {status} |")

        output.append("")
        output.append("---")
        output.append("")

        # Detailed breakdown
        output.append("## Detailed Traceability")
        output.append("")

        for req_id in sorted(self.requirements.keys()):
            req = self.requirements[req_id]
            output.append(f"### {req_id}")
            output.append("")
            output.append(f"**Description**: {req['description']}")
            output.append("")
            output.append(f"**Defined in**: {req['file']}:{req['line']}")
            output.append("")

            # Design references
            if req_id in self.design_refs:
                output.append("**Design**:")
                for file, line in self.design_refs[req_id]:
                    output.append(f"- {file}:{line}")
                output.append("")

            # Code references
            if req_id in self.code_refs:
                output.append("**Implementation**:")
                for file, line in self.code_refs[req_id]:
                    output.append(f"- {file}:{line}")
                output.append("")

            # Test references
            if req_id in self.test_refs:
                output.append("**Tests**:")
                for file, line in self.test_refs[req_id]:
                    output.append(f"- {file}:{line}")
                output.append("")

            output.append("---")
            output.append("")

        return "\n".join(output)

    def print_report(self) -> int:
        """Print validation report. Returns exit code (0 = pass, 1 = fail)."""
        unimplemented, untested, orphaned = self.validate()

        # Summary
        print("=" * 80)
        print("TRACEABILITY VALIDATION REPORT")
        print("=" * 80)
        print()
        print(f"📊 Requirements Summary:")
        print(f"   Total requirements: {len(self.requirements)}")
        print(f"   Design references: {len(self.design_refs)}")
        print(f"   Code implementations: {len(self.code_refs)}")
        print(f"   Test validations: {len(self.test_refs)}")
        print()

        # Issues
        has_issues = False

        if unimplemented:
            has_issues = True
            print(f"❌ Requirements without implementation ({len(unimplemented)}):")
            for req_id in sorted(unimplemented)[:10]:  # Show first 10
                req = self.requirements[req_id]
                print(f"   - {req_id}: {req['description'][:60]}")
            if len(unimplemented) > 10:
                print(f"   ... and {len(unimplemented) - 10} more")
            print()

        if untested:
            has_issues = True
            print(f"⚠️  Requirements without tests ({len(untested)}):")
            for req_id in sorted(untested)[:10]:  # Show first 10
                req = self.requirements[req_id]
                print(f"   - {req_id}: {req['description'][:60]}")
            if len(untested) > 10:
                print(f"   ... and {len(untested) - 10} more")
            print()

        if orphaned:
            has_issues = True
            print(f"🔗 Orphaned references (no matching requirement) ({len(orphaned)}):")
            for req_id in sorted(orphaned):
                print(f"   - {req_id}")
            print()

        # Coverage
        if self.requirements:
            design_coverage = (len(self.design_refs) / len(self.requirements)) * 100
            code_coverage = (len(self.code_refs) / len(self.requirements)) * 100
            test_coverage = (len(self.test_refs) / len(self.requirements)) * 100

            print(f"📈 Coverage:")
            print(f"   Design: {design_coverage:.1f}%")
            print(f"   Implementation: {code_coverage:.1f}%")
            print(f"   Tests: {test_coverage:.1f}%")
            print()

        # Quality gates
        print("🚦 Quality Gates:")
        design_pass = len(self.design_refs) >= len(self.requirements) * 0.8
        code_pass = len(self.code_refs) >= len(self.requirements) * 0.8
        test_pass = len(self.test_refs) >= len(self.requirements) * 0.8

        print(f"   Design ≥80%: {'✅ PASS' if design_pass else '❌ FAIL'}")
        print(f"   Implementation ≥80%: {'✅ PASS' if code_pass else '❌ FAIL'}")
        print(f"   Tests ≥80%: {'✅ PASS' if test_pass else '❌ FAIL'}")
        print()

        print("=" * 80)

        if has_issues or not (design_pass and code_pass and test_pass):
            print("❌ TRACEABILITY VALIDATION FAILED")
            return 1
        else:
            print("✅ TRACEABILITY VALIDATION PASSED")
            return 0


def main():
    parser = argparse.ArgumentParser(description="Validate requirement traceability")
    parser.add_argument('--requirements', type=Path, default=Path('docs/requirements'),
                       help='Requirements directory')
    parser.add_argument('--design', type=Path, default=Path('docs/design'),
                       help='Design directory')
    parser.add_argument('--code', nargs='+', type=Path,
                       default=[Path('installers'), Path('mcp_service'), Path('plugins')],
                       help='Code directories')
    parser.add_argument('--matrix', action='store_true',
                       help='Generate traceability matrix (markdown)')
    parser.add_argument('--inventory', action='store_true',
                       help='Generate component inventory (markdown)')
    parser.add_argument('--check-all', action='store_true',
                       help='Run full validation and report')

    args = parser.parse_args()

    validator = TraceabilityValidator()

    # Extract requirements
    if args.requirements.exists():
        validator.extract_requirements(args.requirements)
    else:
        print(f"❌ Requirements directory not found: {args.requirements}")
        return 1

    # Scan design
    if args.design.exists():
        validator.scan_design_docs(args.design)

    # Scan code
    validator.scan_code(args.code)

    # Output
    if args.matrix:
        print(validator.generate_matrix())
        return 0
    elif args.inventory:
        print(validator.generate_inventory())
        return 0
    elif args.check_all:
        return validator.print_report()
    else:
        # Default: just print summary
        print(f"Requirements: {len(validator.requirements)}")
        print(f"Design refs: {len(validator.design_refs)}")
        print(f"Code refs: {len(validator.code_refs)}")
        print(f"Test refs: {len(validator.test_refs)}")
        return 0


if __name__ == '__main__':
    sys.exit(main())
