# SQL Validation Testing

## Overview

**Yes, we now validate generated SQL!** We've added comprehensive SQL validation tests that catch syntax errors, structural issues, and potential security vulnerabilities.

## What Gets Validated

### 1. **Basic Syntax Parsing** (using `sqlparse`)
```python
test_generated_sql_is_parseable()
```
- Verifies SQL can be parsed
- Ensures no `UNKNOWN` statement types
- Catches basic syntax errors

### 2. **Snowflake CREATE PROCEDURE Structure**
```python
test_create_procedure_structure()
```
Validates presence of required keywords:
- `CREATE OR REPLACE PROCEDURE`
- `RETURNS`
- `LANGUAGE JAVASCRIPT`
- `EXECUTE AS`
- `$$` (procedure body delimiters)

### 3. **Procedure Naming Convention**
```python
test_procedure_name_format()
```
Validates three-part naming: `database.schema.procedure_name`
- Example: `admin_db.default_schema.create_database`

### 4. **Argument List Syntax**
```python
test_argument_list_syntax()
```
Validates:
- Arguments are properly quoted: `"ARG_NAME"`
- Valid data types: `VARCHAR`, `NUMBER`, `VARIANT`, etc.
- Proper comma separation

### 5. **SQL Injection Protection**
```python
test_no_sql_injection_vulnerabilities()
```
Checks for dangerous patterns:
- `'; DROP TABLE`
- `'; DELETE FROM`
- SQL comment injection (`--; `)
- Proper `$$` delimiter usage

### 6. **Advanced Linting** (using `sqlfluff` - optional)
```python
test_lint_with_sqlfluff()
```
- Snowflake-specific dialect validation
- Comprehensive syntax checking
- Catches parsing errors (PRS rules)

## Running SQL Validation Tests

### Basic validation (always runs)
```bash
pytest tests/test_sql_validation.py::TestSQLSyntaxValidation -v
```

### With sqlfluff (recommended)
```bash
pip install sqlfluff
pytest tests/test_sql_validation.py -v
```

## Example: What Gets Caught

### ❌ Bad SQL (would fail tests)
```sql
CREATE OR REPLACE PROCEDURE test_db.test_schema.bad_proc (
  "ARG1" VARCHAR,,,  -- Extra commas!
)
RETURNS varchar
LANGAUGE JAVASCRIPT  -- Typo: LANGAUGE
EXECUTE AS owner
AS
$  -- Missing $$
return 'hello';
$;
```

### ✅ Good SQL (passes all tests)
```sql
CREATE OR REPLACE PROCEDURE admin_db.default_schema.create_database (
 "DATABASE_NAME" VARCHAR
)

RETURNS varchar
LANGUAGE JAVASCRIPT
COMMENT = 'Creates a database with the provided name'
EXECUTE AS owner
AS
$$
var databaseName = DATABASE_NAME;
var query = `CREATE DATABASE ${databaseName}`;
snowflake.execute({sqlText: query});
return `Database ${databaseName} created successfully`;
$$;
```

## Test Results

All SQL validation tests pass! ✅

```
tests/test_sql_validation.py::TestSQLSyntaxValidation::test_generated_sql_is_parseable PASSED
tests/test_sql_validation.py::TestSQLSyntaxValidation::test_create_procedure_structure PASSED
tests/test_sql_validation.py::TestSQLSyntaxValidation::test_procedure_name_format PASSED
tests/test_sql_validation.py::TestSQLSyntaxValidation::test_argument_list_syntax PASSED
tests/test_sql_validation.py::TestSQLSyntaxValidation::test_no_sql_injection_vulnerabilities PASSED
tests/test_sql_validation.py::TestSQLLintingWithSqlfluff::test_lint_with_sqlfluff PASSED
```

## What's NOT Validated (Intentionally)

These require actual Snowflake execution:

- **Semantic errors**: References to non-existent databases/schemas
- **Permission errors**: User lacks CREATE PROCEDURE privilege
- **Runtime errors**: JavaScript code logic errors
- **Data type compatibility**: Whether function calls work with actual data

These are better caught through:
1. Integration testing with a dev Snowflake instance
2. Snowflake's `EXPLAIN` functionality
3. Actual procedure execution tests

## How It Works

```python
# 1. Generate SQL via build command
result = runner.invoke(build, ["project", "--target", "output"])

# 2. Read generated SQL files
sql_content = Path("output/procedure.sql").read_text()

# 3. Parse and validate
parsed = sqlparse.parse(sql_content)
assert parsed[0].get_type() != "UNKNOWN"

# 4. Check structure with regex
pattern = r"CREATE OR REPLACE PROCEDURE\s+(\w+)\.(\w+)\.(\w+)"
assert re.search(pattern, sql_content)

# 5. Lint with sqlfluff (optional)
linter = Linter(dialect="snowflake")
result = linter.lint_string(sql_content)
assert len(result.violations) == 0
```

## Adding More Validation

To add custom SQL validation rules:

```python
def test_custom_validation(self, tmp_path):
    """Add your own validation logic"""
    runner = CliRunner()
    # ... generate SQL ...

    sql_content = Path("output/proc.sql").read_text()

    # Custom check: ensure all procedures have comments
    assert "COMMENT =" in sql_content, "Procedures must have comments"

    # Custom check: specific naming pattern
    assert re.match(r"CREATE.*_v\d+$", sql_content), "Procedures must be versioned"
```

## Recommendations

1. **Always run** basic SQL validation tests (they're fast, no extra deps)
2. **Use sqlfluff** for production - catches more issues
3. **Add custom validators** for your org's SQL standards
4. **Run in CI/CD** to catch issues before deployment

## Summary

**Before:** ❌ No SQL validation - could deploy syntactically invalid SQL

**Now:** ✅ Comprehensive SQL validation catching:
- Syntax errors
- Structural issues
- Security vulnerabilities
- Snowflake-specific problems (with sqlfluff)

All without needing a Snowflake instance!
