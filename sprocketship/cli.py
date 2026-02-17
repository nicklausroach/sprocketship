"""Command-line interface for sprocketship stored procedure management.

Provides CLI commands for deploying stored procedures to Snowflake (liftoff)
and building SQL files locally (build).
"""

import click
import sys
import traceback
from typing import Any, Callable

from snowflake import connector  # type: ignore[import-untyped]
from absql import render_file  # type: ignore[import-untyped]
from pathlib import Path

from .utils import (
    ConfigurationError,
    create_javascript_stored_procedure,
    filter_procedures,
    grant_usage,
    get_file_config,
    quote_identifier,
    validate_procedure_config,
)


def _load_config(directory: str) -> dict[str, Any]:
    """Load and validate configuration file.

    Args:
        directory: Directory containing .sprocketship.yml

    Returns:
        Configuration dictionary with snowflake and procedures sections

    Raises:
        SystemExit: Exits with code 1 if config cannot be loaded
    """
    config_path = Path(directory) / ".sprocketship.yml"
    try:
        return render_file(config_path, return_dict=True)  # type: ignore[no-any-return]
    except FileNotFoundError:
        error_msg = f"""[E001] Configuration file not found: {config_path}

Expected location:
  {config_path.absolute()}

Fix: Create a .sprocketship.yml file with required configuration:
  snowflake:
    account: !env_var SNOWFLAKE_ACCOUNT
    user: !env_var SNOWFLAKE_USER
    password: !env_var SNOWFLAKE_PASSWORD
    role: !env_var SNOWFLAKE_ROLE
    warehouse: !env_var SNOWFLAKE_WAREHOUSE

  procedures:
    +database: YOUR_DATABASE
    +schema: YOUR_SCHEMA
    +language: javascript
    +execute_as: owner
"""
        click.echo(click.style(error_msg, fg="red"), err=True)
        sys.exit(1)
    except Exception:
        msg = click.style("Failed to load configuration: ", fg="red", bold=True)
        msg += click.style(f"{config_path}", fg="white")
        click.echo(msg, err=True)
        click.echo(traceback.format_exc(), err=True)
        sys.exit(1)


def _discover_and_filter_files(directory: str, only: tuple[str, ...]) -> list[Path]:
    """Discover .js files and optionally filter by procedure names.

    Args:
        directory: Directory to search for .js files
        only: Tuple of procedure names to include (if empty, includes all)

    Returns:
        List of Path objects for matching .js files
    """
    files = list(Path(directory).rglob("*.js"))

    # Filter files if --only flag is provided
    files, not_found = filter_procedures(files, only)
    if not_found:
        msg = click.style("Warning: ", fg="yellow", bold=True)
        msg += click.style(f"Could not find procedure(s): {', '.join(sorted(not_found))}", fg="white")
        click.echo(msg, err=True)

    return files


def _process_procedures(
    directory: str,
    config: dict,
    files: list[Path],
    processor: Callable[[dict, dict], None],
    error_verb: str = "failed to process"
) -> bool:
    """Process each procedure file with a custom processor callback.

    Args:
        directory: Base directory for procedures
        config: Configuration dictionary from .sprocketship.yml
        files: List of procedure file paths to process
        processor: Callback function that receives (proc_dict, proc) and handles
                   the actual deployment or build logic
        error_verb: Error message verb to use on failure (e.g., "could not be launched")

    Returns:
        True if any errors occurred, False otherwise
    """
    err = False
    for file in files:
        proc = get_file_config(file, config, directory)
        try:
            # Validate configuration before processing
            validate_procedure_config(proc, proc.get("name", str(file)))

            proc_dict = create_javascript_stored_procedure(
                **proc, **{"project_dir": directory}
            )

            # Call the processor callback to handle deployment or build logic
            processor(proc_dict, proc)

        except ConfigurationError as e:
            err = True
            # ConfigurationError already has nice formatting, so just print it
            click.echo(click.style(str(e), fg="red"), err=True)
        except Exception:
            err = True
            msg = click.style(f"{proc['name']} ", fg="red", bold=True)
            msg += click.style(f"{error_verb}.", fg="white", bold=True)
            click.echo(msg)
            click.echo(traceback.format_exc(), err=True)

    return err


@click.group()
def main() -> None:
    """Main entry point for the sprocketship CLI."""
    pass


@main.command()
@click.argument("directory", default=".")
@click.option("--show", is_flag=True)
@click.option("--only", multiple=True, help="Deploy only specified procedure(s). Can be used multiple times.")
def liftoff(directory: str, show: bool, only: tuple[str, ...]) -> None:
    """Deploy stored procedures to Snowflake.

    Discovers all .js files in the procedures/ directory, renders them
    with configuration from .sprocketship.yml, and executes CREATE PROCEDURE
    statements in Snowflake. Optionally switches roles before deployment
    and grants usage permissions.

    Args:
        directory: Directory containing .sprocketship.yml and procedures/
        show: If True, print rendered SQL to stdout after deployment
        only: Tuple of procedure names to deploy (if empty, deploys all)

    Raises:
        SystemExit: Exits with code 1 if any procedure fails to deploy
    """
    click.echo(click.style("🚀 Sprocketship lifting off!", fg="white", bold=True))

    # Load configuration
    data = _load_config(directory)

    # Connect to Snowflake
    try:
        con = connector.connect(**data["snowflake"])
    except KeyError:
        error_msg = """[E004] Missing 'snowflake' section in configuration file

The configuration file must include a 'snowflake' section with connection details.

Fix: Add to .sprocketship.yml:
  snowflake:
    account: !env_var SNOWFLAKE_ACCOUNT
    user: !env_var SNOWFLAKE_USER
    password: !env_var SNOWFLAKE_PASSWORD
    role: !env_var SNOWFLAKE_ROLE
    warehouse: !env_var SNOWFLAKE_WAREHOUSE

Make sure to set the corresponding environment variables.
"""
        click.echo(click.style(error_msg, fg="red"), err=True)
        sys.exit(1)
    except Exception as e:
        error_msg = f"""[E005] Failed to connect to Snowflake

Error: {e}

Troubleshooting:
  1. Verify environment variables are set:
     - SNOWFLAKE_ACCOUNT
     - SNOWFLAKE_USER
     - SNOWFLAKE_PASSWORD
     - SNOWFLAKE_ROLE
     - SNOWFLAKE_WAREHOUSE

  2. Check network connectivity to Snowflake

  3. Verify credentials are correct
"""
        click.echo(click.style(error_msg, fg="red"), err=True)
        sys.exit(1)

    # Discover and filter procedure files
    files = _discover_and_filter_files(directory, only)

    # Define deployment processor
    def deploy_processor(proc_dict: dict, proc: dict) -> None:
        """Deploy a single procedure to Snowflake."""
        use_role = proc_dict.get('use_role', data['snowflake'].get('role', 'SYSADMIN'))
        con.cursor().execute(f"USE ROLE {quote_identifier(use_role.upper())}")
        con.cursor().execute(proc_dict["rendered_file"])
        if "grant_usage" in proc_dict:
            grant_usage(proc_dict, con)

        msg = click.style(f"{proc_dict['name']} ", fg="green", bold=True)
        msg += click.style("launched into schema ", fg="white", bold=True)
        msg += click.style(
            f"{proc_dict['database']}.{proc_dict['schema']}", fg="blue", bold=True
        )

        click.echo(msg)
        if show:
            click.echo(proc_dict["rendered_file"])

    # Process procedures
    err = _process_procedures(directory, data, files, deploy_processor, "could not be launched")
    sys.exit(1 if err else 0)


@main.command()
@click.argument("directory", default=".")
@click.option("--target", default="target/sprocketship")
@click.option("--only", multiple=True, help="Build only specified procedure(s). Can be used multiple times.")
def build(directory: str, target: str, only: tuple[str, ...]) -> None:
    """Build SQL files locally without deploying to Snowflake.

    Discovers all .js files in the procedures/ directory, renders them
    with configuration from .sprocketship.yml, and writes the resulting
    CREATE PROCEDURE SQL statements to the target directory.

    Args:
        directory: Directory containing .sprocketship.yml and procedures/
        target: Output directory for generated SQL files (relative to directory)
        only: Tuple of procedure names to build (if empty, builds all)

    Raises:
        SystemExit: Exits with code 1 if any procedure fails to build
    """
    click.echo(click.style("⚙️ Building sprocketship!", fg="white", bold=True))

    # Create target directory for rendered procedures
    (Path(directory) / target).mkdir(parents=True, exist_ok=True)

    # Load configuration
    data = _load_config(directory)

    # Discover and filter procedure files
    files = _discover_and_filter_files(directory, only)

    # Define build processor
    def build_processor(proc_dict: dict, proc: dict) -> None:
        """Build a single procedure to SQL file."""
        output_path = Path(directory) / target / f"{proc['name']}.sql"
        output_path.write_text(proc_dict["rendered_file"], encoding="utf-8")
        msg = click.style(f"{proc_dict['name']} ", fg="green", bold=True)
        msg += click.style("successfully built", fg="white", bold=True)
        click.echo(msg)

    # Process procedures
    err = _process_procedures(directory, data, files, build_processor, "could not be built")
    sys.exit(1 if err else 0)
