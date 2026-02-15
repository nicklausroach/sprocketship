# Testing Sprocketship

## Quick Start

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=sprocketship --cov-report=html

# Run specific test file
pytest tests/test_cli.py -v
```

## Test Coverage

Current coverage: **84%**

- **CLI module (cli.py)**: 82% coverage
- **Utils module (utils.py)**: 88% coverage

## What's Tested (No Snowflake Required!)

### ✅ Core Functionality

1. **SQL Syntax Validation** (`test_sql_validation.py`) ⭐ NEW!
   - Basic SQL parsing and syntax checking
   - CREATE PROCEDURE structure validation
   - Snowflake-specific linting (with sqlfluff)
   - SQL injection vulnerability detection
   - See [SQL_VALIDATION.md](tests/SQL_VALIDATION.md) for details

2. **Configuration Loading & Merging** (`test_utils.py`)
   - Hierarchical YAML config resolution
   - Cascading `+` prefix behavior
   - Frontmatter overrides from procedure files
   - Path-based config lookups

3. **Template Rendering** (`test_utils.py`)
   - JavaScript procedure SQL generation
   - Argument handling (uppercase, quoted)
   - Return types and comments
   - Multi-argument procedures

4. **Build Command** (`test_cli.py`)
   - Local SQL generation without Snowflake
   - File discovery and processing
   - Config merging verification
   - Error handling for missing/invalid configs

5. **Liftoff Command** (`test_cli.py`)
   - Full deployment flow (with mocked Snowflake)
   - Role switching logic
   - GRANT USAGE statement generation
   - Error handling and recovery

### Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── test_cli.py              # Integration tests for commands
├── test_utils.py            # Unit tests for core functions
├── fixtures/                # Test data
│   ├── .sprocketship.yml
│   ├── admin/
│   │   ├── create_database.js
│   │   └── drop_database.js
│   └── useradmin/
│       └── create_user.js
└── README.md                # Detailed testing guide
```

## Key Testing Strategies

### 1. Use `build` Command for Integration Testing

The `build` command tests the entire pipeline without Snowflake:

```bash
sprocketship build test-fixtures/ --target test-output
```

This validates:
- Config parsing
- File discovery
- Template rendering
- SQL generation

### 2. Mock Snowflake for Deployment Tests

```python
@patch("sprocketship.cli.connector.connect")
def test_liftoff_with_mock_snowflake(mock_connect, cli_runner, fixture_dir):
    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn
    # Test deployment logic without real database
```

### 3. Unit Test Pure Functions

Functions like `get_file_config()` and `create_javascript_stored_procedure()` are tested independently:

```python
def test_with_real_fixture_structure():
    config = render_file("fixtures/.sprocketship.yml", return_dict=True)
    result = get_file_config(file_path, config, base_dir)
    assert result["database"] == "admin_db"
```

## Running Tests in CI/CD

These tests are perfect for continuous integration:

```yaml
# .github/workflows/test.yml
- name: Run tests
  run: |
    pip install -e ".[dev]"
    pytest --cov=sprocketship --cov-report=xml
```

**No Snowflake credentials required!** All Snowflake interactions are mocked.

## Common Test Patterns

### Testing Config Merging

```python
# Verify cascading + prefixes work
config = {
    "procedures": {
        "+database": "default_db",
        "admin": {
            "+database": "admin_db"  # Overrides parent
        }
    }
}
```

### Testing SQL Generation

```python
result = create_javascript_stored_procedure(
    name="test_proc",
    database="test_db",
    args=[{"name": "arg1", "type": "varchar"}]
)
assert '"ARG1" VARCHAR' in result["rendered_file"]
```

### Testing Error Handling

```python
result = cli_runner.invoke(build, ["."])
assert result.exit_code == 1
assert "Configuration file not found" in result.output
```

## What's NOT Covered

- Actual Snowflake connection and execution (intentionally mocked)
- Network failures and timeouts
- Real database constraint violations

These are handled by mocking and are appropriate for unit/integration testing.

## Adding New Tests

When adding features:

1. **Add unit tests** for pure functions in `test_utils.py`
2. **Add integration tests** for CLI changes in `test_cli.py`
3. **Update fixtures** if testing new config structures
4. **Run with coverage** to ensure new code is tested

```bash
pytest --cov=sprocketship --cov-report=term-missing
```

Look for missing lines in the coverage report and add tests to cover them.
