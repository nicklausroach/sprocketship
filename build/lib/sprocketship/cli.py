import click
import os
import itertools
from snowflake import connector
from absql import render_text
from jinja2 import Environment
from ruamel.yaml import YAML

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
  create_proc_text = '''
CREATE {%if replace_if_exists %}OR REPLACE{% endif %} PROCEDURE {{database}}.{{schema}}.{{name}} (
{%- for arg_name, arg_data_type in args.items() %}
"{{arg_name.upper()}}" {{arg_data_type.upper()}}{%if not loop.last %},{% endif %}
{%- endfor -%}
)
{% if copy_grants %}COPY GRANTS{% endif %}
RETURNS {{returns}}
LANGUAGE JAVASCRIPT
{% if comment %}COMMENT = '{{comment}}'{% endif %}
EXECUTE AS {{execute_as}}
AS '
{{procedure_definition}}' 
  '''
  return render_text(create_proc_text, **kwargs, **procedure_def_dict)




@click.command()
@click.argument("subcommand", type=click.Choice(["liftoff"]))
@click.argument("dir", default=".")
def main(subcommand, dir):
    if subcommand == "liftoff":
        click.echo(click.style(f"🚀 Sprocketship lifting off!", fg='white', bold=True))
        # Open config in current directory

        yaml = YAML(typ='safe')
        with open(os.path.join(dir, '.sprocketship.yml'), 'r') as file:
            data = yaml.load(Environment().from_string(file.read()).render(env=os.environ))

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
            except Exception as e:
                msg = click.style(f"{proc['name']} ", fg='red', bold=True)
                msg += click.style(f"could not be launched into schema ", fg='white', bold=True)
                msg += click.style(f"{proc['database']}.{proc['schema']}", fg='blue', bold=True)
                click.echo(msg)
                click.echo(e, err=True)
