# Test-Driven Development Workflow

## The RED → GREEN → REFACTOR Cycle

This document defines the complete TDD workflow for ai_sdlc_method, adapted from [ai_init](https://github.com/foolishimp/ai_init).

---

## Overview

Test-Driven Development (TDD) is not optional - it's the foundation of how we build software.

**The Cycle**:
```
RED → GREEN → REFACTOR → COMMIT → REPEAT
```

**The Rule**: **"No code without tests"**

---

## The Complete Workflow

### 1️⃣ RED: Write Failing Test

Write a test that defines the desired behavior. The test should fail initially.

**Steps**:
1. Identify what needs to be tested
2. Write the test case
3. Run the test (it should fail)
4. Verify it fails for the right reason

**Example**:
```python
def test_merge_two_hierarchies():
    """Test merging two hierarchies with override precedence."""
    # Arrange
    base = HierarchyNode(path="")
    base.add_child("name", HierarchyNode(path="name", value="BaseApp"))

    override = HierarchyNode(path="")
    override.add_child("name", HierarchyNode(path="name", value="OverrideApp"))

    merger = HierarchyMerger()

    # Act
    result = merger.merge([base, override])

    # Assert
    assert result.get_value_by_path("name") == "OverrideApp"

# Run: pytest tests/test_hierarchy_merger.py::test_merge_two_hierarchies
# Expected: FAIL (merge() not implemented yet)
```

**Red Phase Checklist**:
- [ ] Test is clear and focused
- [ ] Test describes desired behavior
- [ ] Test fails when run
- [ ] Failure reason is correct (not syntax error)

---

### 2️⃣ GREEN: Write Minimal Code

Write just enough code to make the test pass. No more, no less.

**Steps**:
1. Implement the simplest solution
2. Run the test
3. Verify it passes
4. Don't worry about elegance yet

**Example**:
```python
class HierarchyMerger:
    def merge(self, hierarchies: List[HierarchyNode]) -> HierarchyNode:
        """Merge multiple hierarchies with priority."""
        if not hierarchies:
            raise ValueError("Cannot merge empty list")

        # Simplest implementation that passes the test
        if len(hierarchies) == 1:
            return hierarchies[0]

        result = copy.deepcopy(hierarchies[0])
        for hierarchy in hierarchies[1:]:
            # Simple override logic
            for key, child in hierarchy.children.items():
                result.children[key] = copy.deepcopy(child)

        return result

# Run: pytest tests/test_hierarchy_merger.py::test_merge_two_hierarchies
# Expected: PASS
```

**Green Phase Checklist**:
- [ ] Test passes
- [ ] Only necessary code written
- [ ] No premature optimization
- [ ] Focus on functionality, not elegance

---

### 3️⃣ REFACTOR: Improve Code Quality

Now make the code better while keeping tests green.

**Steps**:
1. Look for improvements
2. Refactor one thing at a time
3. Run tests after each change
4. Keep tests passing throughout

**Example**:
```python
class HierarchyMerger:
    def merge(self, hierarchies: List[HierarchyNode]) -> HierarchyNode:
        """
        Merge multiple hierarchies with priority-based overrides.

        Args:
            hierarchies: List of HierarchyNode roots, ordered by priority
                        (first = lowest, last = highest)

        Returns:
            Merged HierarchyNode tree

        Raises:
            ValueError: If hierarchies list is empty
        """
        if not hierarchies:
            raise ValueError("Cannot merge empty list of hierarchies")

        if len(hierarchies) == 1:
            return copy.deepcopy(hierarchies[0])

        # Refactored: Extract method, add documentation
        result = copy.deepcopy(hierarchies[0])
        for i, hierarchy in enumerate(hierarchies[1:], start=1):
            result = self._merge_two_nodes(result, hierarchy, priority=i)

        return result

    def _merge_two_nodes(
        self,
        base: HierarchyNode,
        override: HierarchyNode,
        priority: int
    ) -> HierarchyNode:
        """Merge two nodes recursively."""
        # Clean, extracted logic
        ...

# Run: pytest tests/test_hierarchy_merger.py
# Expected: PASS (all tests still green)
```

**Refactor Phase Checklist**:
- [ ] Code is more readable
- [ ] Duplication removed
- [ ] Names are clear
- [ ] Comments explain "why" not "what"
- [ ] All tests still pass

---

### 4️⃣ COMMIT: Save Progress

Commit your work with a clear, descriptive message.

**Commit Message Format**:
```
<type>: <short summary>

<detailed description>

<test evidence>

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Example**:
```bash
git add tests/test_hierarchy_merger.py src/ai_sdlc_config/mergers/hierarchy_merger.py
git commit -m "feat: implement two-hierarchy merging with priority

Add merge() method to HierarchyMerger that combines two hierarchies
with later configs overriding earlier ones. Implements the foundation
for multi-layer configuration merging.

Tests:
- test_merge_two_hierarchies: PASS
- test_merge_single_hierarchy: PASS
- test_merge_empty_list_raises_error: PASS

Coverage: mergers/hierarchy_merger.py 95%

Co-Authored-By: Claude <noreply@anthropic.com>"
```

**Commit Checklist**:
- [ ] All tests passing
- [ ] Commit message is descriptive
- [ ] Only related changes included
- [ ] No debug code or comments

---

### 5️⃣ REPEAT: Next Test

Start the cycle again with the next test.

**Example Progression**:
```
Test 1: test_merge_two_hierarchies ✅
    → Implement basic merging

Test 2: test_merge_three_hierarchies ✅
    → Extend to multiple hierarchies

Test 3: test_merge_nested_structures ✅
    → Handle deep nesting

Test 4: test_merge_with_uri_references ✅
    → Preserve URI references

...and so on until feature is complete
```

---

## TDD Best Practices

### Test Naming

```python
# ✅ Good: Descriptive, clear intent
def test_merge_two_hierarchies_override_precedence():
    ...

def test_load_yaml_file_not_found_raises_error():
    ...

def test_uri_resolver_caches_content():
    ...

# ❌ Bad: Vague, unclear
def test_merge():
    ...

def test_loader():
    ...

def test_works():
    ...
```

### Test Structure

Use AAA (Arrange-Act-Assert):

```python
def test_example():
    # Arrange: Set up test data
    input_data = create_test_data()
    expected = "expected_result"

    # Act: Perform the operation
    result = function_under_test(input_data)

    # Assert: Verify the result
    assert result == expected
```

### Test Independence

Each test should be independent:

```python
# ✅ Good: Independent tests
def test_merge_case_1():
    merger = HierarchyMerger()  # Fresh instance
    result = merger.merge([base1, override1])
    assert ...

def test_merge_case_2():
    merger = HierarchyMerger()  # Fresh instance
    result = merger.merge([base2, override2])
    assert ...

# ❌ Bad: Tests depend on order
class TestMerger:
    def setup(self):
        self.merger = HierarchyMerger()  # Shared state

    def test_case_1(self):
        self.merger.merge([base1])  # Modifies shared state

    def test_case_2(self):
        self.merger.merge([base2])  # Affected by case_1
```

### Test Coverage

Aim for >80% coverage, but focus on meaningful tests:

```python
# Cover:
- Happy path (normal usage)
- Edge cases (empty, null, boundary values)
- Error conditions (invalid input, missing data)
- Integration points (module interactions)

# Don't obsess over:
- Trivial getters/setters
- Auto-generated code
- Third-party library internals
```

---

## Common Scenarios

### New Feature

```
1. Write test for desired feature → RED
2. Implement feature minimally → GREEN
3. Improve implementation → REFACTOR
4. Add more test cases → RED
5. Handle edge cases → GREEN
6. Polish code → REFACTOR
7. Commit feature
```

### Bug Fix

```
1. Write test that reproduces bug → RED (should fail)
2. Fix the bug → GREEN (test now passes)
3. Add related test cases → RED
4. Verify fix handles all cases → GREEN
5. Refactor if needed → REFACTOR
6. Commit fix
```

### Refactoring

```
1. Ensure all existing tests pass → GREEN
2. Refactor code → Keep tests GREEN throughout
3. Run full test suite → Verify still GREEN
4. Commit refactoring
```

---

## Running Tests

### Quick Commands

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_hierarchy_merger.py

# Run specific test
pytest tests/test_hierarchy_merger.py::test_merge_two_hierarchies

# Watch mode (run on file change)
pytest tests/ --watch

# Coverage report
pytest tests/ --cov=src/ai_sdlc_config --cov-report=html

# Parallel execution
pytest tests/ -n auto
```

### CI/CD Integration

All tests must pass before merging:

```yaml
# .github/workflows/tests.yml
- name: Run tests
  run: pytest tests/ --cov --cov-fail-under=80
```

---

## Metrics

Track your TDD discipline:

| Metric | Target | Current |
|--------|--------|---------|
| Test Coverage | >80% | 100% |
| Tests Passing | 100% | 156/156 |
| Tests per Module | >10 | ✅ |
| Test Execution Time | <5s | 0.16s |

---

## Anti-Patterns to Avoid

### ❌ Writing Code First

```python
# Wrong order:
1. Write implementation
2. Write tests
3. Fix implementation to pass tests

# This defeats the purpose of TDD!
```

### ❌ Testing Implementation Details

```python
# Bad: Tests internal implementation
def test_merge_uses_deepcopy():
    assert merger._called_deepcopy == True

# Good: Tests behavior
def test_merge_does_not_mutate_originals():
    result = merger.merge([base, override])
    assert base.get_value("name") == "original"
```

### ❌ Overly Complex Tests

```python
# Bad: Test does too much
def test_entire_system():
    # 100 lines of test code
    # Tests multiple features
    # Hard to debug when it fails

# Good: Focused test
def test_merge_two_hierarchies():
    # 10 lines
    # Tests one thing
    # Clear what failed if it breaks
```

---

## Summary

**The TDD Mantra**: RED → GREEN → REFACTOR

1. **RED**: Write failing test
2. **GREEN**: Make it pass
3. **REFACTOR**: Make it better
4. **COMMIT**: Save progress
5. **REPEAT**: Next test

**No code without tests. Ever.**

---

## References

- **Origin**: [ai_init TDD Process](https://github.com/foolishimp/ai_init)
- **Applied In**: All ai_sdlc_method development
- **Test Suite**: [tests/](../../tests/)
- **Key Principles**: [KEY_PRINCIPLES.md](../principles/KEY_PRINCIPLES.md)

---

*TDD is not just a practice - it's a discipline. Master it.*
