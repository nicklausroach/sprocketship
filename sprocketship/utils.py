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


def get_file_config(path: Path, config: dict, dir: str):
    filename = path.stem
    keys = ["procedures"] + str(path.relative_to(dir)).split("/")[:-1] + [filename]

    file_config = {"path": str(path), "name": filename}
    curr_config = config
    for key in keys:
        file_config.update(
            {k[1:]: v for k, v in curr_config.items() if k.startswith("+")}
        )
        if key in curr_config:
            curr_config = curr_config[key]
        else:
            return file_config
    file_config.update(curr_config)
    return file_config


def get_full_file_path(proc_config):
    extension_map = {"javascript": ".js", "python": ".py"}
    file_name = proc_config["name"] + extension_map[proc_config["language"]]
    return os.path.join("procedures", proc_config["path"], file_name)


def get_file_contents(fpath, extra_context):
    return render_file(fpath, return_dict=True, extra_context=extra_context)


def create_javascript_stored_procedure(**kwargs):
    # Render the javascript file
    file_contents = render_file(kwargs["path"], return_dict=True)
    procedure_def_dict = {"procedure_definition": file_contents["absql_body"]}

    context = kwargs
    context.update(file_contents)
    context.update(procedure_def_dict)

    # Render the stored procedure template with the procedure definition
    rendered_file = render_file(
        os.path.join(Path(__file__).parent, "templates/javascript.sql"), **context
    )
    return {**kwargs, "rendered_file": rendered_file}


def grant_usage(proc, con):
    types = [arg["type"] for arg in proc["args"]]
    types_str = f"({','.join(types)})"
    for grantee_type in proc["grant_usage"]:
        for grantee in proc["grant_usage"][grantee_type]:
            query = f"GRANT USAGE ON PROCEDURE {proc['database']}.{proc['schema']}.{proc['name']}{types_str} TO {grantee_type} {grantee}"
            con.cursor().execute(query)
