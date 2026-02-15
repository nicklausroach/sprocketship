"""Utility functions for sprocketship stored procedure management.

This module provides helper functions for configuration merging, file path
resolution, template rendering, and Snowflake permission grants.
"""

import os
from typing import Any

from absql import render_file
from pathlib import Path


def get_file_config(path: Path, config: dict[str, Any], dir: str) -> dict[str, Any]:
    """Merge hierarchical configuration for a procedure file.

    Walks through the config tree matching the file path structure,
    collecting default configs (prefixed with '+') and merging them
    with procedure-specific configs.

    Args:
        path: Path to the procedure file
        config: Parsed configuration from .sprocketship.yml
        dir: Base directory path

    Returns:
        Merged configuration dictionary with 'path' and 'name' keys
    """
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


def get_full_file_path(proc_config: dict[str, Any]) -> str:
    """Construct full file path for a procedure from its configuration.

    Args:
        proc_config: Procedure configuration dictionary containing 'name', 'language', and 'path'

    Returns:
        Full file path string (e.g., "procedures/sysadmin/create_db.js")
    """
    extension_map = {"javascript": ".js", "python": ".py"}
    file_name = proc_config["name"] + extension_map[proc_config["language"]]
    return os.path.join("procedures", proc_config["path"], file_name)


def get_file_contents(fpath: str, extra_context: dict[str, Any]) -> dict[str, Any]:
    """Load and render a file with ABSQL, including frontmatter parsing.

    Args:
        fpath: Path to the file to render
        extra_context: Additional context variables for template rendering

    Returns:
        Dictionary containing rendered content and metadata
    """
    return render_file(fpath, return_dict=True, extra_context=extra_context)


def create_javascript_stored_procedure(**kwargs: Any) -> dict[str, Any]:
    """Generate a complete CREATE PROCEDURE SQL statement for a JavaScript procedure.

    Renders the procedure file (extracting frontmatter), then renders the
    Jinja2 template with the procedure body to produce the final SQL.

    Args:
        **kwargs: Procedure configuration including 'path', 'name', 'args', 'returns', etc.

    Returns:
        Dictionary containing original kwargs plus 'rendered_file' with complete SQL
    """
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


def grant_usage(proc: dict[str, Any], con: Any) -> None:
    """Execute GRANT USAGE statements for a procedure.

    Grants procedure usage permissions to specified roles and users.

    Args:
        proc: Procedure dictionary containing 'grant_usage', 'database', 'schema', 'name', 'args'
        con: Snowflake connection object
    """
    types = [arg["type"] for arg in proc["args"]]
    types_str = f"({','.join(types)})"
    for grantee_type in proc["grant_usage"]:
        for grantee in proc["grant_usage"][grantee_type]:
            query = f"GRANT USAGE ON PROCEDURE {proc['database']}.{proc['schema']}.{proc['name']}{types_str} TO {grantee_type} {grantee}"
            con.cursor().execute(query)
