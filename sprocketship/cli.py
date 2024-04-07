import click
import os
import itertools
from snowflake import connector
from absql import render_file
from pathlib import Path

def extract_configs(data, path=''):
    configs = {}
    for key, value in data.items():
        new_path = f"{path}/{key}" if path else key
        if isinstance(value, list):
            configs[new_path] = value
            for item in value:
                item["path"] = new_path
        elif isinstance(value, dict):
            configs.update(extract_configs(value, new_path))
    return configs


def get_full_file_path(proc_config):
    extension_map = {
        'javascript': '.js',
        'python': '.py'
    }
    file_name = proc_config['name'] + extension_map[proc_config['language']]
    return os.path.join("procedures", proc_config["path"], file_name)


def get_file_contents(fpath):
    with open(fpath, 'r') as file:
        return file.read()


def create_javascript_stored_procedure(**kwargs):
    path = os.path.join(kwargs['project_dir'], get_full_file_path(kwargs))
    procedure_def_dict = {'procedure_definition': get_file_contents(path)}
    return render_file(os.path.join(Path(__file__).parent, "templates/javascript.sql"), **kwargs, **procedure_def_dict)


@click.group()
def main():
    pass

@main.command()
@click.argument("dir", default=".")
@click.option('--show', is_flag=True)
def liftoff(dir, show):
    click.echo(click.style(f"🚀 Sprocketship lifting off!", fg='white', bold=True))
    # Open config in current directory

    data = render_file(os.path.join(dir, '.sprocketship.yml'), return_dict=True)

    con = connector.connect(**data["snowflake"])

    # Get the configurations for each procedure and attach relative path to file directory
    configs_with_paths = extract_configs(data["procedures"])
    procs = list(itertools.chain(*configs_with_paths.values()))

    for proc in procs:
        try:
            rendered_proc = create_javascript_stored_procedure(**proc, **{'project_dir': dir})
            con.cursor().execute(rendered_proc)
            msg = click.style(f"{proc['name']} ", fg='green', bold=True)
            msg += click.style(f"launched into schema ", fg='white', bold=True)
            msg += click.style(f"{proc['database']}.{proc['schema']}", fg='blue', bold=True)
            click.echo(msg)
            if show:
                click.echo(rendered_proc)
        except Exception as e:
            msg = click.style(f"{proc['name']} ", fg='red', bold=True)
            msg += click.style(f"could not be launched into schema ", fg='white', bold=True)
            msg += click.style(f"{proc['database']}.{proc['schema']}", fg='blue', bold=True)
            click.echo(msg)
            click.echo(e, err=True)
            click.echo(rendered_proc)


@main.command()
@click.argument("dir", default=".")
@click.option("--target", default="target/sprocketship")
def build(dir, target):
    click.echo(click.style(f"⚙️ Building sprocketship!", fg='white', bold=True))
    # Open config in current directory

    Path(os.path.join(dir, target)).mkdir(parents=True, exist_ok=True)

    data = render_file(os.path.join(dir, '.sprocketship.yml'), return_dict=True)

    # Get the configurations for each procedure and attach relative path to file directory
    configs_with_paths = extract_configs(data["procedures"])
    procs = list(itertools.chain(*configs_with_paths.values()))

    for proc in procs:
        try:
            rendered_proc = create_javascript_stored_procedure(**proc, **{'project_dir': dir})
            with open(os.path.join(dir, target, proc["name"] + ".sql"), '+a') as f:
                f.write(rendered_proc)
            msg = click.style(f"{proc['name']} ", fg='green', bold=True)
            msg += click.style(f"successfully built", fg='white', bold=True)
            click.echo(msg)
        except Exception as e:
            msg = click.style(f"{proc['name']} ", fg='red', bold=True)
            msg += click.style(f"could not be built", fg='white', bold=True)
            click.echo(msg)
            click.echo(e, err=True)
