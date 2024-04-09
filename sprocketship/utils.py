import os
from absql import render_file
from pathlib import Path


def extract_configs(data, path=""):
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
    extension_map = {"javascript": ".js", "python": ".py"}
    file_name = proc_config["name"] + extension_map[proc_config["language"]]
    return os.path.join("procedures", proc_config["path"], file_name)


def get_file_contents(fpath):
    with open(fpath, "r") as file:
        return file.read()


def create_javascript_stored_procedure(**kwargs):
    path = os.path.join(kwargs["project_dir"], get_full_file_path(kwargs))
    procedure_def_dict = {"procedure_definition": get_file_contents(path)}
    return render_file(
        os.path.join(Path(__file__).parent, "templates/javascript.sql"),
        **kwargs,
        **procedure_def_dict,
    )

def grant_usage(proc, con):
    types = [arg['type'] for arg in proc['args']]
    types_str = f"({','.join(types)})"
    for grantee_type in proc['grant_usage']:
        for grantee in proc['grant_usage'][grantee_type]:
            query = f"GRANT USAGE ON PROCEDURE {proc['database']}.{proc['schema']}.{proc['name']}{types_str} TO {grantee_type} {grantee}"
            con.cursor().execute(query)
