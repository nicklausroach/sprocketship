import click
import os
import itertools
from snowflake import connector
from absql import render_file
from pathlib import Path
import traceback

from .utils import (
    extract_configs,
    create_javascript_stored_procedure,
    grant_usage,
    get_file_config,
)


@click.group()
@click.pass_context
def main(ctx):
    """Sprocketship CLI - Manage Snowflake stored procedures with ease.

    Sprocketship is a Python CLI tool for managing Snowflake stored procedures.
    It separates procedure code from configuration, uses Jinja2 templating to
    generate CREATE PROCEDURE statements, and supports hierarchical configuration
    with file frontmatter overrides.
    """
    pass


@main.command()
@click.argument("dir", default=".")
@click.option("--show", is_flag=True)
def liftoff(dir, show):
    """Deploy Snowflake procedures from a directory.

    Discovers all .js procedure files in the specified directory, renders them
    with their configuration, and deploys them to Snowflake. Supports role
    switching per procedure and optional GRANT USAGE statements.

    The command will:
    1. Load .sprocketship.yml configuration from the directory
    2. Connect to Snowflake using credentials from the config
    3. Find all .js files recursively in the directory
    4. For each procedure:
       - Merge hierarchical configuration
       - Switch to the appropriate role if specified
       - Execute CREATE PROCEDURE statement
       - Grant usage permissions if configured
    5. Exit with code 1 if any procedure fails, 0 if all succeed

    Args:
        dir: Directory containing procedures and .sprocketship.yml
             (default: current directory)
        show: If True, print the rendered SQL for each procedure

    Example:
        sprocketship liftoff ./procedures
        sprocketship liftoff ./procedures --show
    """
    click.echo(click.style(f"🚀 Sprocketship lifting off!", fg="white", bold=True))

    config_path = os.path.join(dir, ".sprocketship.yml")
    try:
        data = render_file(config_path, return_dict=True)
    except FileNotFoundError:
        msg = click.style("Configuration file not found: ", fg="red", bold=True)
        msg += click.style(f"{config_path}", fg="white")
        click.echo(msg, err=True)
        exit(1)
    except Exception as e:
        msg = click.style("Failed to load configuration: ", fg="red", bold=True)
        msg += click.style(f"{config_path}", fg="white")
        click.echo(msg, err=True)
        click.echo(traceback.format_exc(), err=True)
        exit(1)

    try:
        con = connector.connect(**data["snowflake"])
    except KeyError:
        msg = click.style("Missing 'snowflake' section in configuration file", fg="red", bold=True)
        click.echo(msg, err=True)
        exit(1)
    except Exception as e:
        msg = click.style("Failed to connect to Snowflake: ", fg="red", bold=True)
        msg += click.style(str(e), fg="white")
        click.echo(msg, err=True)
        exit(1)

    files = list(Path(dir).rglob("*.js"))

    err = False
    for file in files:
        proc = get_file_config(file, data, dir)
        try:
            proc_dict = create_javascript_stored_procedure(
                **proc, **{"project_dir": dir}
            )
            if "use_role" in proc.keys():
                con.cursor().execute(f"USE ROLE {proc_dict['use_role'].upper()}")
            else:
                con.cursor().execute(f"USE ROLE {data['snowflake']['role']}")
            con.cursor().execute(proc_dict["rendered_file"])
            if "grant_usage" in proc_dict.keys():
                grant_usage(proc_dict, con)

            msg = click.style(f"{proc_dict['name']} ", fg="green", bold=True)
            msg += click.style(f"launched into schema ", fg="white", bold=True)
            msg += click.style(
                f"{proc_dict['database']}.{proc_dict['schema']}", fg="blue", bold=True
            )

            click.echo(msg)
            if show:
                click.echo(proc_dict["rendered_file"])
        except Exception as e:
            err = True
            msg = click.style(f"{proc['name']} ", fg="red", bold=True)
            msg += click.style(f"could not be launched.", fg="white", bold=True)
            click.echo(msg)
            click.echo(traceback.format_exc(), err=True)
    exit(1 if err else 0)


@main.command()
@click.argument("dir", default=".")
@click.option("--target", default="target/sprocketship")
def build(dir, target):
    """Build procedure SQL files locally without deploying to Snowflake.

    Discovers all .js procedure files in the specified directory, renders them
    with their configuration, and writes the resulting SQL to local files in
    the target directory. This is useful for reviewing generated SQL before
    deployment or for version control of rendered procedures.

    The command will:
    1. Load .sprocketship.yml configuration from the directory
    2. Create the target directory if it doesn't exist
    3. Find all .js files recursively in the directory
    4. For each procedure:
       - Merge hierarchical configuration
       - Render the CREATE PROCEDURE statement
       - Write the SQL to a .sql file in the target directory
    5. Exit with code 1 if any procedure fails, 0 if all succeed

    Args:
        dir: Directory containing procedures and .sprocketship.yml
             (default: current directory)
        target: Output directory for rendered SQL files
                (default: target/sprocketship)

    Example:
        sprocketship build ./procedures
        sprocketship build ./procedures --target ./output
    """
    click.echo(click.style(f"⚙️ Building sprocketship!", fg="white", bold=True))

    # Create target directory for rendered procedures
    Path(os.path.join(dir, target)).mkdir(parents=True, exist_ok=True)

    config_path = os.path.join(dir, ".sprocketship.yml")
    try:
        data = render_file(config_path, return_dict=True)
    except FileNotFoundError:
        msg = click.style("Configuration file not found: ", fg="red", bold=True)
        msg += click.style(f"{config_path}", fg="white")
        click.echo(msg, err=True)
        exit(1)
    except Exception as e:
        msg = click.style("Failed to load configuration: ", fg="red", bold=True)
        msg += click.style(f"{config_path}", fg="white")
        click.echo(msg, err=True)
        click.echo(traceback.format_exc(), err=True)
        exit(1)

    files = list(Path(dir).rglob("*.js"))

    err = False
    for file in files:
        proc = get_file_config(file, data, dir)
        try:
            proc_dict = create_javascript_stored_procedure(
                **proc, **{"project_dir": dir}
            )
            with open(os.path.join(dir, target, proc["name"] + ".sql"), "w") as f:
                f.write(proc_dict["rendered_file"])
            msg = click.style(f"{proc_dict['name']} ", fg="green", bold=True)
            msg += click.style(f"successfully built", fg="white", bold=True)
            click.echo(msg)
        except Exception as e:
            err = True
            msg = click.style(f"{proc['name']} ", fg="red", bold=True)
            msg += click.style(f"could not be built", fg="white", bold=True)
            click.echo(msg)
            click.echo(traceback.format_exc(), err=True)
    exit(1 if err else 0)
