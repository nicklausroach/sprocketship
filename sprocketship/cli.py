"""Command-line interface for sprocketship stored procedure management.

Provides CLI commands for deploying stored procedures to Snowflake (liftoff)
and building SQL files locally (build).
"""

import click
import sys
import traceback

from snowflake import connector  # type: ignore[import-untyped]
from absql import render_file  # type: ignore[import-untyped]
from pathlib import Path

from .utils import (
    create_javascript_stored_procedure,
    filter_procedures,
    grant_usage,
    get_file_config,
    quote_identifier,
    validate_procedure_config,
)


@click.group()
@click.pass_context
def main(ctx: click.Context) -> None:
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

    config_path = Path(directory) / ".sprocketship.yml"
    try:
        data = render_file(config_path, return_dict=True)
    except FileNotFoundError:
        msg = click.style("Configuration file not found: ", fg="red", bold=True)
        msg += click.style(f"{config_path}", fg="white")
        click.echo(msg, err=True)
        sys.exit(1)
    except Exception:
        msg = click.style("Failed to load configuration: ", fg="red", bold=True)
        msg += click.style(f"{config_path}", fg="white")
        click.echo(msg, err=True)
        click.echo(traceback.format_exc(), err=True)
        sys.exit(1)

    try:
        con = connector.connect(**data["snowflake"])
    except KeyError:
        msg = click.style("Missing 'snowflake' section in configuration file", fg="red", bold=True)
        click.echo(msg, err=True)
        sys.exit(1)
    except Exception as e:
        msg = click.style("Failed to connect to Snowflake: ", fg="red", bold=True)
        msg += click.style(str(e), fg="white")
        click.echo(msg, err=True)
        sys.exit(1)


    files = list(Path(directory).rglob("*.js"))

    # Filter files if --only flag is provided
    files, not_found = filter_procedures(files, only)
    if not_found:
        msg = click.style("Warning: ", fg="yellow", bold=True)
        msg += click.style(f"Could not find procedure(s): {', '.join(sorted(not_found))}", fg="white")
        click.echo(msg, err=True)

    err = False
    for file in files:
        proc = get_file_config(file, data, directory)
        try:
            # Validate configuration before processing
            validate_procedure_config(proc, proc.get("name", str(file)))

            proc_dict = create_javascript_stored_procedure(
                **proc, **{"project_dir": directory}
            )
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
        except Exception:
            err = True
            msg = click.style(f"{proc['name']} ", fg="red", bold=True)
            msg += click.style("could not be launched.", fg="white", bold=True)
            click.echo(msg)
            click.echo(traceback.format_exc(), err=True)
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

    config_path = Path(directory) / ".sprocketship.yml"
    try:
        data = render_file(config_path, return_dict=True)
    except FileNotFoundError:
        msg = click.style("Configuration file not found: ", fg="red", bold=True)
        msg += click.style(f"{config_path}", fg="white")
        click.echo(msg, err=True)
        sys.exit(1)
    except Exception:
        msg = click.style("Failed to load configuration: ", fg="red", bold=True)
        msg += click.style(f"{config_path}", fg="white")
        click.echo(msg, err=True)
        click.echo(traceback.format_exc(), err=True)
        sys.exit(1)


    files = list(Path(directory).rglob("*.js"))

    # Filter files if --only flag is provided
    files, not_found = filter_procedures(files, only)
    if not_found:
        msg = click.style("Warning: ", fg="yellow", bold=True)
        msg += click.style(f"Could not find procedure(s): {', '.join(sorted(not_found))}", fg="white")
        click.echo(msg, err=True)

    err = False
    for file in files:
        proc = get_file_config(file, data, directory)
        try:
            # Validate configuration before processing
            validate_procedure_config(proc, proc.get("name", str(file)))

            proc_dict = create_javascript_stored_procedure(
                **proc, **{"project_dir": directory}
            )
            output_path = Path(directory) / target / f"{proc['name']}.sql"
            output_path.write_text(proc_dict["rendered_file"], encoding="utf-8")
            msg = click.style(f"{proc_dict['name']} ", fg="green", bold=True)
            msg += click.style("successfully built", fg="white", bold=True)
            click.echo(msg)
        except Exception:
            err = True
            msg = click.style(f"{proc['name']} ", fg="red", bold=True)
            msg += click.style("could not be built", fg="white", bold=True)
            click.echo(msg)
            click.echo(traceback.format_exc(), err=True)
    sys.exit(1 if err else 0)
