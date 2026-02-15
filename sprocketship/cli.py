"""Command-line interface for sprocketship stored procedure management.

Provides CLI commands for deploying stored procedures to Snowflake (liftoff)
and building SQL files locally (build).
"""

import click
import sys
import traceback

from snowflake import connector
from absql import render_file
from pathlib import Path

from .utils import (
    create_javascript_stored_procedure,
    grant_usage,
    get_file_config,
)


@click.group()
@click.pass_context
def main(ctx: click.Context) -> None:
    """Main entry point for the sprocketship CLI."""
    pass


@main.command()
@click.argument("dir", default=".")
@click.option("--show", is_flag=True)
def liftoff(dir: str, show: bool) -> None:
    """Deploy stored procedures to Snowflake.

    Discovers all .js files in the procedures/ directory, renders them
    with configuration from .sprocketship.yml, and executes CREATE PROCEDURE
    statements in Snowflake. Optionally switches roles before deployment
    and grants usage permissions.

    Args:
        dir: Directory containing .sprocketship.yml and procedures/
        show: If True, print rendered SQL to stdout after deployment

    Raises:
        SystemExit: Exits with code 1 if any procedure fails to deploy
    """
    click.echo(click.style("🚀 Sprocketship lifting off!", fg="white", bold=True))
    config_path = Path(dir) / ".sprocketship.yml"
    data = render_file(config_path, return_dict=True)
    con = connector.connect(**data["snowflake"])
    files = list(Path(dir).rglob("*.js"))

    err = False
    for file in files:
        proc = get_file_config(file, data, dir)
        try:
            proc_dict = create_javascript_stored_procedure(
                **proc, **{"project_dir": dir}
            )
            use_role = proc_dict.get('use_role', data['snowflake']['role'])
            con.cursor().execute(f"USE ROLE {use_role.upper()}")
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
@click.argument("dir", default=".")
@click.option("--target", default="target/sprocketship")
def build(dir: str, target: str) -> None:
    """Build SQL files locally without deploying to Snowflake.

    Discovers all .js files in the procedures/ directory, renders them
    with configuration from .sprocketship.yml, and writes the resulting
    CREATE PROCEDURE SQL statements to the target directory.

    Args:
        dir: Directory containing .sprocketship.yml and procedures/
        target: Output directory for generated SQL files (relative to dir)

    Raises:
        SystemExit: Exits with code 1 if any procedure fails to build
    """
    click.echo(click.style("⚙️ Building sprocketship!", fg="white", bold=True))
    # Open config in current directory

    (Path(dir) / target).mkdir(parents=True, exist_ok=True)

    config_path = Path(dir) / ".sprocketship.yml"
    data = render_file(config_path, return_dict=True)
    files = list(Path(dir).rglob("*.js"))

    err = False
    for file in files:
        proc = get_file_config(file, data, dir)
        try:
            proc_dict = create_javascript_stored_procedure(
                **proc, **{"project_dir": dir}
            )
            output_path = Path(dir) / target / f"{proc['name']}.sql"
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
