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
    pass


@main.command()
@click.argument("dir", default=".")
@click.option("--show", is_flag=True)
def liftoff(dir, show):
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
