import os
from absql import render_file
from pathlib import Path


def extract_configs(data, path=""):
    """Recursively extract configurations from nested dictionary structure.

    Traverses a nested dictionary and builds a flat mapping of paths to values.
    For list values, adds a 'path' key to each list item. For dict values,
    recursively processes them to build deeper paths.

    Args:
        data: Dictionary to extract configurations from
        path: Current path string being built (empty for root level)

    Returns:
        Dictionary mapping path strings to their values

    Example:
        >>> data = {"procedures": {"sysadmin": {"proc1": {...}}}}
        >>> extract_configs(data)
        {"procedures/sysadmin/proc1": {...}}
    """
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
    """Merge hierarchical configuration for a procedure file.

    Walks through the config tree matching the file path structure,
    collecting default configs (prefixed with '+') and merging them
    with procedure-specific configs. This creates a complete configuration
    by inheriting cascading defaults and applying file-specific overrides.

    Args:
        path: Path object for the procedure file
        config: Parsed configuration dictionary from .sprocketship.yml
        dir: Base directory path

    Returns:
        Dictionary containing merged configuration for the procedure,
        including 'path' and 'name' keys.

    Example:
        >>> path = Path("procedures/sysadmin/create_db.js")
        >>> config = {"procedures": {"+database": "my_db", "sysadmin": {...}}}
        >>> result = get_file_config(path, config, ".")
        >>> result['database']  # inherited from +database default
        'my_db'
    """
    filename = path.stem
    relative_path = path.relative_to(dir)
    # Use Path.parts for cross-platform compatibility
    path_parts = list(relative_path.parts[:-1])  # Exclude filename from parts
    keys = ["procedures"] + path_parts + [filename]

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
    """Construct the full file path for a procedure based on its configuration.

    Builds the complete file path by combining the procedures directory,
    the procedure's path, and filename with the appropriate extension
    based on the language setting.

    Args:
        proc_config: Dictionary containing procedure configuration with
                    'name', 'language', and 'path' keys

    Returns:
        String representing the full file path to the procedure file

    Example:
        >>> config = {"name": "create_db", "language": "javascript", "path": "sysadmin"}
        >>> get_full_file_path(config)
        'procedures/sysadmin/create_db.js'
    """
    extension_map = {"javascript": ".js", "python": ".py"}
    file_name = proc_config["name"] + extension_map[proc_config["language"]]
    return os.path.join("procedures", proc_config["path"], file_name)


def get_file_contents(fpath, extra_context):
    """Read and render a file with ABSQL, including frontmatter parsing.

    Uses ABSQL's render_file to read a file and parse any frontmatter,
    returning both the file content and parsed metadata as a dictionary.

    Args:
        fpath: File path to read and render
        extra_context: Additional context dictionary to pass to the renderer

    Returns:
        Dictionary containing parsed file contents and metadata
    """
    return render_file(fpath, return_dict=True, extra_context=extra_context)


def create_javascript_stored_procedure(**kwargs):
    """Generate a complete CREATE PROCEDURE SQL statement for a JavaScript procedure.

    Combines the procedure's JavaScript code with the SQL template to create
    a complete Snowflake CREATE PROCEDURE statement. The process involves:
    1. Rendering the JavaScript file with ABSQL to extract the procedure body
    2. Merging the procedure code with configuration parameters
    3. Rendering the Jinja2 SQL template to produce the final SQL

    Args:
        **kwargs: Procedure configuration including:
            - path: File path to the JavaScript procedure
            - database: Target Snowflake database
            - schema: Target Snowflake schema
            - name: Procedure name
            - args: List of argument definitions
            - returns: Return type specification
            - execute_as: Execution context (owner/caller)
            - Additional configuration from .sprocketship.yml

    Returns:
        Dictionary containing all input kwargs plus 'rendered_file' key
        with the complete SQL CREATE PROCEDURE statement

    Example:
        >>> create_javascript_stored_procedure(
        ...     path="procedures/create_db.js",
        ...     database="my_db",
        ...     schema="public",
        ...     name="create_db",
        ...     args=[{"name": "db_name", "type": "varchar"}],
        ...     returns="varchar"
        ... )
        {..., 'rendered_file': 'CREATE OR REPLACE PROCEDURE...'}
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


def grant_usage(proc, con):
    """Execute GRANT USAGE statements for a procedure to specified roles/users.

    Grants usage permissions on a Snowflake procedure to the roles and users
    specified in the procedure configuration. The procedure is identified by
    its full signature including argument types.

    Args:
        proc: Procedure configuration dictionary containing:
            - database: Database name
            - schema: Schema name
            - name: Procedure name
            - args: List of argument definitions with 'type' keys
            - grant_usage: Dictionary with 'role' and/or 'user' keys,
                          each containing a list of grantees
        con: Active Snowflake database connection

    Example:
        >>> proc = {
        ...     "database": "my_db",
        ...     "schema": "public",
        ...     "name": "my_proc",
        ...     "args": [{"type": "varchar"}],
        ...     "grant_usage": {
        ...         "role": ["analyst_role"],
        ...         "user": ["john_doe"]
        ...     }
        ... }
        >>> grant_usage(proc, snowflake_connection)
        # Executes: GRANT USAGE ON PROCEDURE my_db.public.my_proc(varchar) TO role analyst_role
        # Executes: GRANT USAGE ON PROCEDURE my_db.public.my_proc(varchar) TO user john_doe
    """
    types = [arg["type"] for arg in proc["args"]]
    types_str = f"({','.join(types)})"
    for grantee_type in proc["grant_usage"]:
        for grantee in proc["grant_usage"][grantee_type]:
            query = f"GRANT USAGE ON PROCEDURE {proc['database']}.{proc['schema']}.{proc['name']}{types_str} TO {grantee_type} {grantee}"
            con.cursor().execute(query)
