import click
import os
import itertools
from snowflake import connector
from absql import render_file
from pathlib import Path

from .utils import extract_configs, create_javascript_stored_procedure


@click.group()
@click.pass_context
def main(ctx):
    pass


@main.command()
@click.argument("dir", default=".")
@click.option("--show", is_flag=True)
def liftoff(dir, show):
    click.echo(click.style(f"🚀 Sprocketship lifting off!", fg="white", bold=True))
    # Open config in current directory

    data = render_file(os.path.join(dir, ".sprocketship.yml"), return_dict=True)

    con = connector.connect(**data["snowflake"])

    # Get the configurations for each procedure and attach relative path to file directory
    configs_with_paths = extract_configs(data["procedures"])
    procs = list(itertools.chain(*configs_with_paths.values()))

    err = False
    for proc in procs:
        try:
            rendered_proc = create_javascript_stored_procedure(
                **proc, **{"project_dir": dir}
            )
            con.cursor().execute(rendered_proc)
            msg = click.style(f"{proc['name']} ", fg="green", bold=True)
            msg += click.style(f"launched into schema ", fg="white", bold=True)
            msg += click.style(
                f"{proc['database']}.{proc['schema']}", fg="blue", bold=True
            )
            click.echo(msg)
            if show:
                click.echo(rendered_proc)
        except Exception as e:
            err = True
            msg = click.style(f"{proc['name']} ", fg="red", bold=True)
            msg += click.style(
                f"could not be launched into schema ", fg="white", bold=True
            )
            msg += click.style(
                f"{proc['database']}.{proc['schema']}", fg="blue", bold=True
            )
            click.echo(msg)
            click.echo(e, err=True)
            click.echo(rendered_proc)
    exit(1 if err else 0)


@main.command()
@click.argument("dir", default=".")
@click.option("--target", default="target/sprocketship")
def build(dir, target):
    click.echo(click.style(f"⚙️ Building sprocketship!", fg="white", bold=True))
    # Open config in current directory

    Path(os.path.join(dir, target)).mkdir(parents=True, exist_ok=True)

    data = render_file(os.path.join(dir, ".sprocketship.yml"), return_dict=True)

    # Get the configurations for each procedure and attach relative path to file directory
    configs_with_paths = extract_configs(data["procedures"])
    procs = list(itertools.chain(*configs_with_paths.values()))

    err = False
    for proc in procs:
        try:
            rendered_proc = create_javascript_stored_procedure(
                **proc, **{"project_dir": dir}
            )
            with open(os.path.join(dir, target, proc["name"] + ".sql"), "+a") as f:
                f.write(rendered_proc)
            msg = click.style(f"{proc['name']} ", fg="green", bold=True)
            msg += click.style(f"successfully built", fg="white", bold=True)
            click.echo(msg)
        except Exception as e:
            err = True
            msg = click.style(f"{proc['name']} ", fg="red", bold=True)
            msg += click.style(f"could not be built", fg="white", bold=True)
            click.echo(msg)
            click.echo(e, err=True)
    exit(1 if err else 0)
