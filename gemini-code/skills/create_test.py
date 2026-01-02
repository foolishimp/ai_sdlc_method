#!/usr/bin/env python
"""
Executable Skill: Create Test

This script creates a new test file based on a requirement ID.
It's designed to be called by the Gemini CLI agent.

Usage:
    python gemini-code/skills/create_test.py --requirement REQ-F-AUTH-001 --path tests/test_auth.py

Implements the executable part of a "skill" as per ADR-008.
The Gemini agent should read the corresponding claude-code prompt for the
goal, then execute this script to perform the action.
"""
import argparse
import os

def main():
    parser = argparse.ArgumentParser(description="Create a test file for a requirement.")
    parser.add_argument("--requirement", required=True, help="The requirement ID (e.g., REQ-F-AUTH-001)")
    parser.add_argument("--path", required=True, help="The path for the new test file")
    args = parser.parse_args()

    content = f'''"""
Test for {args.requirement}
"""

# Validates: {args.requirement}

import pytest

def test_placeholder_for_{args.requirement.replace('-', '_')}():
    """
    Placeholder test for {args.requirement}.
    This test should be updated to properly validate the requirement.
    """
    assert False, "Test not implemented for {args.requirement}"

'''

    try:
        os.makedirs(os.path.dirname(args.path), exist_ok=True)
        with open(args.path, "w") as f:
            f.write(content)
        print(f"Successfully created test file: {args.path}")

        # Make the script executable
        os.chmod(__file__, 0o755)

    except Exception as e:
        print(f"Error creating test file: {e}")
        exit(1)

if __name__ == "__main__":
    main()
