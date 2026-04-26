# CI Failure Patterns and Fixes

This reference documents common CI failure patterns and how to fix them.

## Pre-commit Hook Failures

### Ruff / Black / isort

**Pattern:**
```
ruff....................................................................Failed
- src/app/service.py:45:80: E501 line too long (85 > 79 characters)
```

**Fix:**
- Run `ruff format .` and `ruff check --fix .` to auto-fix
- For line length issues, break long lines or use implicit string concatenation

### mypy

**Pattern:**
```
mypy....................................................................Failed
src/app/service.py:10: error: Argument 1 has incompatible type "str"; expected "int"
```

**Fix:**
- Add proper type annotations
- Fix type mismatches
- Use `# type: ignore[error-code]` only as last resort with explanation

### Flake8

**Pattern:**
```
Flake8..................................................................Failed
src/app/service.py:15:1: F401 'unused_import' imported but unused
```

**Fix:**
- Remove unused imports
- Use `# noqa: F401` only if import is needed for re-export

### gitlint

**Pattern:**
```
gitlint.................................................................Failed
1: T1 Title exceeds max length (75>72)
```

**Fix:**
- Shorten commit title to ≤72 characters
- Amend commit: `git commit --amend`

## pytest Failures

### Test Failures

**Pattern:**
```
FAILED src/tests/test_service.py::TestClass::test_method
AssertionError: assert 100 == 200
```

**Fix:**
- Read the test to understand what's being tested
- Check if the fix broke expected behavior
- Update test if expectations changed (rare)
- Fix the code if test is correct

### Import Errors

**Pattern:**
```
ImportError: cannot import name 'SomeClass' from 'module'
```

**Fix:**
- Check if file was renamed/moved
- Update import statements
- Ensure `__init__.py` exports are correct

### Database Errors

**Pattern:**
```
django.db.utils.IntegrityError: duplicate key value violates unique constraint
```

**Fix:**
- Check if test creates duplicate data
- Use unique values in test data
- Clean up test data in teardown

## Docker Build Failures

**Pattern:**
```
ERROR: failed to solve: process "/bin/sh -c pip install -r requirements.txt" did not complete successfully
```

**Fix:**
- Check if new dependencies were added
- Ensure requirements file is valid
- Check for dependency conflicts

## Coverage Failures

**Pattern:**
```
FAILED: Coverage is 98.5%, required 100%
```

**Fix:**
- Add tests for uncovered lines
- Check coverage report for which lines need testing
- Review which branches need test cases
