# Sprocketship Tests

This directory contains the test suite for Sprocketship.

## Test Structure

- `test_utils.py` - Unit tests for core utility functions (config merging, SQL generation)
- `test_cli.py` - Integration tests for CLI commands (build and liftoff)
- `fixtures/` - Test data (sample configs and procedure files)
- `conftest.py` - Shared pytest fixtures

## Running Tests

### Install Test Dependencies

```bash
pip install -e ".[dev]"
```

### Run All Tests

```bash
pytest
```

### Run with Coverage

```bash
pytest --cov=sprocketship --cov-report=html
```

### Run Specific Test Files

```bash
pytest tests/test_utils.py
pytest tests/test_cli.py
```

### Run Specific Test Classes or Functions

```bash
pytest tests/test_utils.py::TestGetFileConfig
pytest tests/test_cli.py::TestBuildCommand::test_build_with_fixtures
```

### Verbose Output

```bash
pytest -v
pytest -vv  # Extra verbose
```

## What Gets Tested Without Snowflake

✅ **Config Loading & Merging**
- Hierarchical config resolution
- Cascading `+` prefix behavior
- Frontmatter overrides
- Path-based config lookups

✅ **Template Rendering**
- SQL generation from Jinja2 templates
- Procedure argument handling
- Comment formatting
- JavaScript code injection

✅ **File Discovery**
- Recursive `.js` file finding
- Path normalization

✅ **CLI Commands**
- `build` command (full integration test)
- `liftoff` command (with mocked Snowflake connection)
- Error handling
- Role switching logic
- Grant usage SQL generation

## Test Coverage Goals

The test suite focuses on:
1. Pure function logic (no external dependencies)
2. Config merging correctness (common source of bugs)
3. SQL generation accuracy
4. Error handling and edge cases
5. CLI behavior with mocked Snowflake

## Writing New Tests

When adding new features:
1. Add unit tests for pure functions to `test_utils.py`
2. Add integration tests for CLI changes to `test_cli.py`
3. Update fixtures if needed for new test scenarios
4. Mock external dependencies (Snowflake, file system when appropriate)

## Continuous Integration

These tests run without requiring:
- Snowflake credentials
- Active database connections
- External services

This makes them perfect for CI/CD pipelines!
