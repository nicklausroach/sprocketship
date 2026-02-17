# Sprocketship Example Project

This directory contains a complete example project demonstrating Sprocketship's features and configuration patterns.

## Overview

This example includes stored procedures organized by Snowflake role, showcasing:
- **Configuration patterns**: Both YAML and frontmatter approaches
- **Role switching**: Different procedures deployed with different roles
- **Argument handling**: With and without defaults
- **Grant patterns**: Controlling procedure access
- **Cascading defaults**: DRY configuration with `+` prefix

## Project Structure

```
example/
├── .sprocketship.yml          # Configuration with detailed comments
├── .env.example               # Environment variable template
├── README.md                  # This file
└── procedures/
    ├── sysadmin/              # System administration procedures
    │   ├── create_database.js
    │   ├── create_warehouse.js
    │   └── drop_database.js
    └── useradmin/             # User and role management procedures
        ├── create_role.js
        ├── grant_role.js
        └── revoke_role.js
```

## Prerequisites

1. **Snowflake Account**: You need access to a Snowflake account
2. **Required Roles**: Your user should have (or be able to switch to):
   - `SYSADMIN` role for database/warehouse operations
   - `USERADMIN` role for role management operations
3. **Sprocketship Installed**: Install with `pip install sprocketship`

## Setup

1. **Configure Environment Variables**:
   ```bash
   # Copy the template
   cp .env.example .env

   # Edit .env with your credentials
   vim .env  # or your preferred editor
   ```

2. **Verify Configuration**:
   ```bash
   # Check that your credentials work
   sprocketship liftoff --dry-run
   ```

## Usage

### Deploy All Procedures

Deploy all procedures to Snowflake:
```bash
sprocketship liftoff
```

### Preview Generated SQL

See the SQL that will be executed without connecting to Snowflake:
```bash
sprocketship liftoff --dry-run
```

Show SQL during deployment:
```bash
sprocketship liftoff --show
```

### Deploy Specific Procedures

Deploy only specific procedure(s):
```bash
sprocketship liftoff --only create_database
sprocketship liftoff --only create_database,create_role
```

### Build Locally Without Deploying

Generate SQL files locally without connecting to Snowflake:
```bash
sprocketship build
# Output: target/sprocketship/*.sql

# Or specify custom output directory
sprocketship build --target ./output
```

## What Each Procedure Does

### Sysadmin Procedures (deployed with `sysadmin` role)

- **`create_database`**: Creates a new database
  - Arguments: `database_name` (varchar)
  - Example call: `CALL create_database('MY_NEW_DB')`
  - Config: Frontmatter pattern

- **`create_warehouse`**: Creates a virtual warehouse
  - Arguments: `warehouse_name` (varchar), `warehouse_size` (varchar, default 'XSMALL'), `auto_suspend` (number, default 300)
  - Example call: `CALL create_warehouse('MY_WH', 'SMALL', 600)`
  - Config: YAML pattern with defaults

- **`drop_database`**: Drops an existing database (destructive!)
  - Arguments: `database_name` (varchar)
  - Example call: `CALL drop_database('OLD_DB')`
  - Config: YAML pattern with grant_usage

### Useradmin Procedures (deployed with `useradmin` role)

- **`create_role`**: Creates a new role
  - Arguments: `role_name` (varchar)
  - Example call: `CALL create_role('DATA_ANALYST')`
  - Config: Frontmatter pattern

- **`grant_role`**: Grants a role to a user
  - Arguments: `role_name` (varchar), `user_name` (varchar)
  - Example call: `CALL grant_role('DATA_ANALYST', 'john.doe')`
  - Config: YAML pattern

- **`revoke_role`**: Revokes a role from a user
  - Arguments: `role_name` (varchar), `user_name` (varchar)
  - Example call: `CALL revoke_role('DATA_ANALYST', 'john.doe')`
  - Config: YAML pattern with grant_usage

## Testing the Example

After deploying, you can test the procedures in Snowflake:

```sql
-- Switch to appropriate role
USE ROLE sysadmin;

-- Create a test database
CALL create_database('TEST_EXAMPLE_DB');

-- Create a warehouse
CALL create_warehouse('TEST_WH', 'XSMALL', 300);

-- Switch to useradmin role
USE ROLE useradmin;

-- Create a role
CALL create_role('TEST_ANALYST');

-- Grant role to a user (replace with actual username)
CALL grant_role('TEST_ANALYST', 'your_username');

-- Clean up
USE ROLE sysadmin;
CALL drop_database('TEST_EXAMPLE_DB');
DROP WAREHOUSE IF EXISTS TEST_WH;

USE ROLE useradmin;
DROP ROLE IF EXISTS TEST_ANALYST;
```

## Configuration Patterns Demonstrated

### 1. Cascading Defaults (+ prefix)
```yaml
procedures:
  +database: !env_var SNOWFLAKE_DATABASE   # Applies to all procedures
  +language: javascript

  sysadmin:
    +use_role: sysadmin                    # Applies to all sysadmin procedures
```

### 2. Frontmatter Configuration
See `create_database.js` and `create_role.js` for examples of configuration in file frontmatter.

### 3. YAML Configuration
See `create_warehouse.js` and `grant_role.js` for examples of configuration in the YAML file.

### 4. Arguments with Defaults
`create_warehouse` shows how to provide default values for optional arguments.

### 5. Grant Usage Patterns
`drop_database` and `revoke_role` demonstrate controlling who can execute procedures.

## Next Steps

- Modify the example procedures to fit your needs
- Add your own procedures following the patterns shown
- Explore the configuration options in `.sprocketship.yml`
- Read the [main Sprocketship documentation](../../README.md)

## Troubleshooting

**Connection errors**: Verify your `.env` file has correct credentials and your user has the necessary privileges.

**Role switching fails**: Ensure your user can switch to `sysadmin` and `useradmin` roles.

**Procedure creation fails**: Check that you're using the correct database and schema names, and that they exist.

**Environment variables not loading**: Make sure you're loading the `.env` file (Sprocketship uses the `!env_var` tag which reads from your environment).

## Learn More

For more information about Sprocketship features and configuration options, see the main [README](../../README.md).
