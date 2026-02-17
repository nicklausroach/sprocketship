# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Sprocketship is a Python CLI tool for managing Snowflake stored procedures. It separates procedure code from configuration, uses Jinja2 templating to generate CREATE PROCEDURE statements, and supports hierarchical configuration with file frontmatter overrides.

## Coding Standards

**All code changes MUST align with dignified Python standards.**

### Core Principles
1. **LBYL over EAFP**: Always check conditions before acting, never use exceptions for control flow
   - ✅ Use `if key in mapping:` or `.get(key, default)`
   - ❌ Never use try/except KeyError for dictionary access
2. **Pathlib everywhere**: Always use `pathlib.Path`, never `os.path`
   - Always specify encoding: `path.read_text(encoding="utf-8")`
3. **CLI patterns**:
   - Use `click.echo()` (never `print()`)
   - Use `err=True` for error output
   - Use `sys.exit(1)` for error exits
4. **Type hints required**: All functions must have parameter and return type annotations
5. **Exceptions only at error boundaries**: CLI/API level, third-party API wrapping, or adding context before re-raising

### When to Review Standards
Use the `/dignified-python` skill when:
- Writing or reviewing Python code
- Unsure about exception handling patterns
- Working with paths, imports, or CLI code
- Before submitting PRs

## Core Commands

### Deploy to Snowflake
```bash
sprocketship liftoff [DIR]                  # Deploy procedures from DIR (default: current directory)
sprocketship liftoff [DIR] --show           # Show rendered SQL during deployment
sprocketship liftoff [DIR] --dry-run        # Preview SQL without connecting to Snowflake
sprocketship liftoff --only PROC_NAME       # Deploy only specific procedure(s)
```

### Build Locally Without Deploying
```bash
sprocketship build [DIR]                # Build to target/sprocketship/
sprocketship build [DIR] --target PATH  # Build to custom output directory
```

### Development
```bash
pip install -e .                        # Install in development mode
python -m sprocketship.cli liftoff      # Run CLI directly for testing
```

## Architecture

### Core Flow
1. **Config Loading**: `render_file()` from ABSQL loads `.sprocketship.yml` with `!env_var` support
2. **File Discovery**: Recursively finds all `.js` files in project directory
3. **Config Merging**: `get_file_config()` merges hierarchical YAML configs with file frontmatter
4. **Template Rendering**: `create_javascript_stored_procedure()` renders Jinja2 template with procedure code
5. **Deployment**: Connects to Snowflake, switches roles if needed, executes CREATE PROCEDURE, optionally grants usage

### Key Files
- `cli.py` - Click-based CLI with `liftoff` and `build` commands
- `utils.py` - Core logic:
  - `get_file_config()`: Merges hierarchical config from YAML path matching file path
  - `create_javascript_stored_procedure()`: Combines ABSQL-rendered procedure body with Jinja2 template
  - `grant_usage()`: Executes GRANT USAGE statements for roles/users
- `templates/javascript.sql` - Jinja2 template for CREATE PROCEDURE statements

### Configuration Hierarchy
Configs are resolved in this order (later overrides earlier):
1. YAML configs prefixed with `+` (cascade down directory tree)
2. YAML configs at procedure level (exact path match)
3. Frontmatter in procedure `.js` files

Example file path: `procedures/sysadmin/create_database.js`
YAML path: `procedures.sysadmin.create_database`

## Configuration Structure

### Required `.sprocketship.yml` Structure
```yaml
snowflake:
  account: !env_var SNOWFLAKE_ACCOUNT
  user: !env_var SNOWFLAKE_USER
  password: !env_var SNOWFLAKE_PASSWORD
  role: !env_var SNOWFLAKE_ROLE      # Default role for connection
  warehouse: !env_var SNOWFLAKE_WAREHOUSE

procedures:
  +database: value          # + prefix = cascading default for all procedures
  +schema: value
  +language: javascript     # Currently only javascript supported
  +execute_as: owner        # or caller

  subdirectory_name:        # Must match procedures/ directory structure
    +use_role: sysadmin     # Role to switch to before executing CREATE PROCEDURE

    procedure_name:         # Must match .js filename (without extension)
      args:                 # Can also be defined in frontmatter
        - name: arg_name
          type: varchar
          default: optional_value
      returns: varchar
      comment: |
        Multi-line comment
      grant_usage:          # Optional: grant procedure access
        role:
          - role_name
        user:
          - user_name
```

### Procedure File Frontmatter
Files in `procedures/` can override config with frontmatter:
```javascript
/*
args:
  - name: database_name
    type: varchar
returns: varchar
comment: |
  Creates a database with the provided name
*/
var databaseName = DATABASE_NAME;  // Args are accessible as UPPER_SNAKE_CASE
// procedure code...
```

## Important Implementation Details

### Language Support
- **JavaScript**: Fully supported (uses `templates/javascript.sql`)
- **Python**: Not yet implemented (mentioned in README as coming soon)

### Role Switching
- If `use_role` is in procedure config, CLI switches to that role before CREATE PROCEDURE
- Otherwise, uses default role from `snowflake.role` in config
- This allows different procedures to be owned by different roles (e.g., sysadmin vs useradmin)

### ABSQL Integration
- ABSQL handles frontmatter parsing and returns `absql_body` (code without frontmatter)
- ABSQL supports `!env_var` tags in YAML for environment variable substitution
- File rendering is done twice: once for procedure code, once for final SQL template

### Error Handling
- CLI catches exceptions per-procedure and continues processing remaining procedures
- Exits with code 1 if any procedure fails
- Tracebacks printed to stderr for debugging

## Dependencies
- `click` - CLI framework
- `snowflake-connector-python` - Snowflake database connector
- `ABSQL` - File rendering with frontmatter support
- `ruamel.yaml` - YAML parsing with custom tags
- `jinja2` - SQL template rendering

## Common Issues

### File Path Mismatches
The YAML structure must mirror the `procedures/` directory structure:
- File: `procedures/sysadmin/create_db.js`
- YAML: `procedures.sysadmin.create_db`

### Environment Variables
All Snowflake credentials use `!env_var` in `.sprocketship.yml`. Ensure these are set before running `liftoff`.

### Procedure Arguments
- In frontmatter/YAML: use lowercase with underscores (e.g., `database_name`)
- In JavaScript code: use UPPER_SNAKE_CASE (e.g., `DATABASE_NAME`)
