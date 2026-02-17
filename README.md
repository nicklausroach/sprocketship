<!-- Improved compatibility of back to top link: See: https://github.com/othneildrew/Best-README-Template/pull/73 -->
<a name="readme-top"></a>
<!--
*** Thanks for checking out the Best-README-Template. If you have a suggestion
*** that would make this better, please fork the repo and create a pull request
*** or simply open an issue with the tag "enhancement".
*** Don't forget to give the project a star!
*** Thanks again! Now go create something AMAZING! :D
-->



<!-- PROJECT SHIELDS -->
<!--
*** I'm using markdown "reference style" links for readability.
*** Reference links are enclosed in brackets [ ] instead of parentheses ( ).
*** See the bottom of this document for the declaration of the reference variables
*** for contributors-url, forks-url, etc. This is an optional, concise syntax you may use.
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
-->
[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![LinkedIn][linkedin-shield]][linkedin-url]



<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/nicklausroach/sprocketship" style="font-size: 60px; text-decoration: none;">
    <img src="./sprocketship/resources/logo.webp" width='500'>
  </a>
<h3 align="center">Sprocketship</h3>

  <p align="center">
    Better stored procedure management
  </p>
</div>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#commands">Commands</a></li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#development">Development</a></li>
    <li><a href="#troubleshooting">Troubleshooting</a></li>
    <li><a href="#support">Support</a></li>
    <li><a href="#license">License</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

`sprocketship` makes it easy to develop, manage, and deploy stored procedures in Snowflake. Using the language of your choosing, you can write the contents of your stored procedure separately from its configurations (e.g., `EXECUTE AS`, `RETURN TYPE`, etc.). 




### Built With

<a href=https://github.com/pipeline-tools/ABSQL>
<img src=https://raw.githubusercontent.com/pipeline-tools/ABSQL/598fcab4a5ccb1ca674c40e740b4edd9f99251a6/images/logo_400.svg width='150'>
</a>

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- GETTING STARTED -->
## Getting Started

### Installation

`pip install sprocketship`



<!-- COMMANDS -->
## Commands

### Deploy Procedures to Snowflake

```bash
sprocketship liftoff [DIR]
```

Deploys all stored procedures from `DIR` (defaults to current directory) to Snowflake. Sprocketship will process all `.js` files found in the directory tree and execute CREATE PROCEDURE statements.

**Options:**
- `--show` - Display the rendered SQL for each procedure during deployment
- `--dry-run` - Preview what would be deployed without connecting to Snowflake or executing SQL
- `--only PROCEDURE_NAME` - Deploy only specified procedure(s). Can be used multiple times.

**Behavior:**
- If a procedure fails to deploy, sprocketship will continue processing remaining procedures
- Exit code 1 if any procedure fails, 0 if all succeed
- Role switching: Uses `use_role` from config if specified, otherwise uses default role from `snowflake.role`

```bash
# Deploy from current directory
sprocketship liftoff

# Deploy from specific directory
sprocketship liftoff ./my_procedures

# Deploy and show generated SQL
sprocketship liftoff --show

# Preview what would be deployed without connecting to Snowflake
sprocketship liftoff --dry-run

# Deploy only specific procedures
sprocketship liftoff --only create_database --only drop_database
```

### Build Procedures Locally

```bash
sprocketship build [DIR]
```

Generates SQL files for all procedures without deploying to Snowflake. Useful for reviewing generated SQL, version control, or CI/CD pipelines.

**Options:**
- `--target PATH` - Custom output directory (defaults to `target/sprocketship/`)

**Output:**
- Creates one `.sql` file per procedure with the full CREATE PROCEDURE statement
- Files are named `{procedure_name}.sql`

```bash
# Build to default location (target/sprocketship/)
sprocketship build

# Build to custom location
sprocketship build --target ./output/procedures
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- USAGE EXAMPLES -->
## Usage

### Project Structure

Sprocketship requires a `.sprocketship.yml` configuration file at the root of your project directory (where you run the `sprocketship` command). Your stored procedures should be organized in subdirectories.

```
my_project/
├── dbt_models/
│   ├── customers.sql
│   └── products.sql
├── procedures/
│   ├── useradmin/
│   │   ├── create_database_writer_role.js
│   │   └── create_database_reader_role.js
│   └── sysadmin/
│       └── create_temp_database.js
└── .sprocketship.yml
```

**Important:** The YAML path to each procedure in `.sprocketship.yml` must mirror the file path structure in your `procedures/` directory. For example:
- File: `procedures/sysadmin/create_temp_database.js`
- YAML path: `procedures.sysadmin.create_temp_database` 

```yml
procedures:
  development:
    create_temp_database:
      database: !env_var SNOWFLAKE_DATABASE
      schema: !env_var SNOWFLAKE_SCHEMA
      ...

  admin:
    create_database_reader:
      database: !env_var SNOWFLAKE_DATABASE
      schema: !env_var SNOWFLAKE_SCHEMA
      ...

    create_database_writer:
      database: !env_var SNOWFLAKE_DATABASE
      schema: !env_var SNOWFLAKE_SCHEMA
      ...
```

**Note on Environment Variables:** The `!env_var` tag is provided by ABSQL and substitutes environment variables at runtime. Make sure required environment variables are set before running sprocketship commands:

```bash
export SNOWFLAKE_DATABASE=my_database
export SNOWFLAKE_SCHEMA=my_schema
export SNOWFLAKE_ACCOUNT=my_account
# ... etc
```

### Directory-level Default Parameters (Cascading Defaults with `+` Prefix)

Sprocketship uses a **`+` prefix** to mark parameters as cascading defaults. These defaults are inherited by all procedures in subdirectories, greatly reducing configuration duplication.

**How it works:**
- Parameters prefixed with `+` cascade down the directory tree
- Child directories inherit parent defaults unless they override them
- Individual procedures can override any inherited default
- Configuration priority (highest to lowest):
  1. File frontmatter (in the `.js` file itself)
  2. Direct procedure config (exact YAML path match)
  3. Cascading defaults from parent directories (closer ancestors override distant ones)

```yml
procedures:
  # for all procedures, default to the below database and schema
  +database: !env_var SNOWFLAKE_DATABASE
  +schema: !env_var SNOWFLAKE_SCHEMA
  development:
    # for all procedures in the development directory,
    # default to using the sysadmin role
    +use_role: sysadmin
    create_temp_database:
      args:
        - name: Name of argument
          type: Type of argument
          default: (Optional) default value for the argument
      returns: varchar
```

### File Frontmatter

Thanks to ABSQL, sprocketship also provides the ability to define parameters using file frontmatter. Suppose we have a file `create_database_writer_role.js`, we can define parameters for the stored procedure within the file using frontmatter:

```js
/*
database: my_database
schema: my_schema
language: javascript
execute_as: owner
use_role: sysadmin
*/
```

sprocketship will automatically parse and apply the parameters defined in the frontmatter to the stored procedure.

### Recommended Configuration

When setting up your sprocketship project, we recommend setting more general parameters (e.g., database, schema, language, etc.) in the `.sprocketship.yml` file, and anything that's specific to a given procedure should be defined in the file frontmatter of that procedure, such as the args or return type. Example below:

```yml
# .sprocketship.yml
procedures:
  +database: my_database
  +schema: my_schema
  +language: javascript
  +execute_as: owner
  sysadmin:
    +use_role: sysadmin
  useradmin:
    +use_role: useradmin
```

In the above `.sprocketship.yml`, we've set the database, schema, language, and executor at the highest level. This means that all procedures in the `sysadmin` and `useradmin` directories will inherit these defaults unless overridden. Now we can define procedure-specific
parameters in the file frontmatter:

```js
// procedures/useradmin/create_role.js
/*
args:
  - name: role_name
    type: varchar
returns: varchar
comment: |
  Creates a role with the provided name
*/

var roleName = ROLE_NAME;
snowflake.execute(`CREATE ROLE IF NOT EXISTS ${roleName}`)
```

### Exhaustive Options for Stored Procedure Configuration

```yml
database: my_database                    # Database where procedure will be stored
schema: my_schema                        # Schema where procedure will be stored
language: javascript                     # Language of the procedure (currently only javascript)
execute_as: owner                        # 'owner' or 'caller'
use_role: sysadmin                       # Role to switch to before creating procedure
copy_grants: true                        # (Optional) Copy grants from existing procedure
args:                                    # Procedure arguments
  - name: arg_name                       # Argument name (use snake_case)
    type: varchar                        # Snowflake data type
    default: optional_value              # (Optional) default value
returns: varchar                         # Return type (can include NOT NULL)
comment: |                               # (Optional) procedure description
  Multi-line comment describing
  what this procedure does
grant_usage:                             # (Optional) Grant usage after creation
  role:                                  # Grant to roles
    - analyst_role
    - developer_role
  user:                                  # Grant to users
    - john.doe@company.com
```

**Example with grant_usage:**

```yml
procedures:
  +database: analytics
  +schema: procedures
  +language: javascript
  +execute_as: owner

  utilities:
    format_phone_number:
      args:
        - name: phone_number
          type: varchar
      returns: varchar
      comment: Formats a phone number to standard format
      grant_usage:
        role:
          - analyst_role
          - reporting_role
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- DEVELOPMENT -->
## Development

### Local Development Setup

```bash
# Clone the repository
git clone https://github.com/nicklausroach/sprocketship.git
cd sprocketship

# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Or use the Makefile
make install
```

### Code Quality Checks

The project includes several tools to maintain code quality:

```bash
# Run all checks (recommended before committing)
make check

# Run individual checks
make test          # Run tests with pytest
make lint          # Run ruff linter
make type-check    # Run mypy type checker
make dead-code     # Detect unused code with vulture

# Format code
make format        # Auto-format with ruff
```

**Automated checks:**
- **pytest** - Comprehensive test suite
- **mypy** - Static type checking
- **ruff** - Fast linting and formatting
- **vulture** - Dead code detection (finds unused functions, variables, imports)

### Running CLI Directly

When developing, you can run the CLI module directly:

```bash
python -m sprocketship.cli liftoff
python -m sprocketship.cli build
```

### Testing

The project includes a comprehensive test suite covering:
- Configuration hierarchy and merging
- SQL template rendering and validation
- CLI command execution
- ABSQL integration

Run tests before submitting pull requests:

```bash
pytest tests/
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- TROUBLESHOOTING -->
## Troubleshooting

### File Path Mismatches

**Problem:** Procedure not found or configuration not applied.

**Solution:** Ensure your YAML structure mirrors the `procedures/` directory structure exactly:
- File: `procedures/sysadmin/create_db.js`
- YAML: `procedures.sysadmin.create_db` (no `.js` extension in YAML)

### Environment Variables Not Found

**Problem:** `!env_var` tags not substituting values.

**Solution:** Ensure all required environment variables are exported before running sprocketship:

```bash
export SNOWFLAKE_ACCOUNT=my_account
export SNOWFLAKE_USER=my_user
export SNOWFLAKE_PASSWORD=my_password
export SNOWFLAKE_ROLE=my_role
export SNOWFLAKE_WAREHOUSE=my_warehouse
```

### Argument Name Mismatches

**Problem:** Procedure arguments not accessible in JavaScript code.

**Solution:** Remember the naming convention:
- In YAML/frontmatter: `snake_case` (e.g., `database_name`)
- In JavaScript code: `UPPER_SNAKE_CASE` (e.g., `DATABASE_NAME`)

```js
/*
args:
  - name: database_name
    type: varchar
*/
// Access as:
var dbName = DATABASE_NAME;
```

### Role Permission Issues

**Problem:** Procedure creation fails with permission errors.

**Solution:** Use the `use_role` parameter to switch to an appropriate role before creating the procedure:

```yml
procedures:
  sysadmin:
    +use_role: sysadmin
    create_database:
      # procedure config...
```

### Partial Deployment Failures

**Behavior:** When one procedure fails, sprocketship continues processing remaining procedures and exits with code 1.

**What to check:**
- Review the error traceback for the failed procedure
- Verify all required parameters are present
- Check Snowflake permissions for the role being used
- Test the procedure SQL locally using `sprocketship build --show`

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- SUPPORT -->
## Support

sprocketship currently only supports Javascript-based stored procedures (Python support coming soon!). Additionally, there are a few options from the `CREATE STORED PROCEDURE` function that are not yet supported:

* `CALLED ON NULL INPUT | { RETURNS NULL ON NULL INPUT | STRICT }`
* `VOLATILE | IMMUTABLE` (deprecated)


<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/nicklausroach/sprocketship.svg?style=for-the-badge
[contributors-url]: https://github.com/nicklausroach/sprocketship/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/nicklausroach/sprocketship.svg?style=for-the-badge
[forks-url]: https://github.com/nicklausroach/sprocketship/network/members
[stars-shield]: https://img.shields.io/github/stars/nicklausroach/sprocketship.svg?style=for-the-badge
[stars-url]: https://github.com/nicklausroach/sprocketship/stargazers
[issues-shield]: https://img.shields.io/github/issues/nicklausroach/sprocketship.svg?style=for-the-badge
[issues-url]: https://github.com/nicklausroach/sprocketship/issues
[license-shield]: https://img.shields.io/github/license/nicklausroach/sprocketship.svg?style=for-the-badge
[license-url]: https://github.com/nicklausroach/sprocketship/blob/main/LICENSE
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://linkedin.com/in/nicklausroach
