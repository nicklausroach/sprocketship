"""Utility functions for sprocketship stored procedure management.

This module provides helper functions for configuration merging, file path
resolution, template rendering, and Snowflake permission grants.
"""

from typing import Any, Protocol

from absql import render_file  # type: ignore[import-untyped]
from pathlib import Path


class SnowflakeConnection(Protocol):
    """Protocol for Snowflake database connection objects.

    This protocol defines the interface for Snowflake connections used
    in this module. The actual implementation is provided by the
    snowflake-connector-python library.
    """

    def cursor(self) -> Any:
        """Return a cursor object for executing SQL statements.

        Returns:
            Cursor object for SQL execution
        """
        ...


def validate_procedure_config(proc: dict[str, Any], filename: str) -> None:
    """Validate that procedure configuration has all required fields.

    Args:
        proc: Procedure configuration dictionary
        filename: Filename for error messages

    Raises:
        ValueError: If required field is missing or invalid
    """
    required_fields = ["database", "schema", "returns", "language", "execute_as"]
    missing = [field for field in required_fields if field not in proc or proc[field] is None]

    if missing:
        raise ValueError(
            f"Procedure '{filename}' is missing required configuration: {', '.join(missing)}"
        )

    # Validate language is supported
    if proc["language"] not in ["javascript", "python"]:
        raise ValueError(
            f"Procedure '{filename}' has unsupported language: {proc['language']}. "
            f"Supported languages: javascript, python"
        )

    # Validate execute_as value
    if proc["execute_as"] not in ["owner", "caller"]:
        raise ValueError(
            f"Procedure '{filename}' has invalid execute_as value: {proc['execute_as']}. "
            f"Must be 'owner' or 'caller'"
        )


def quote_identifier(identifier: str) -> str:
    """Quote a Snowflake identifier to prevent SQL injection.

    Wraps identifiers in double quotes and escapes any internal double quotes
    by doubling them, following Snowflake's identifier quoting rules.

    Args:
        identifier: The identifier to quote (database, schema, role, etc.)

    Returns:
        Properly quoted identifier safe for use in SQL statements

    Example:
        >>> quote_identifier("my_database")
        '"my_database"'
        >>> quote_identifier('my"weird"name')
        '"my""weird""name"'
    """
    # Escape internal double quotes by doubling them
    escaped = identifier.replace('"', '""')
    return f'"{escaped}"'


def get_file_config(path: Path, config: dict[str, Any], directory: str) -> dict[str, Any]:
    """Merge hierarchical configuration for a procedure file.

    Walks through the config tree matching the file path structure,
    collecting default configs (prefixed with '+') and merging them
    with procedure-specific configs.

    Args:
        path: Path to the procedure file
        config: Parsed configuration from .sprocketship.yml
        directory: Base directory path

    Returns:
        Merged configuration dictionary with 'path' and 'name' keys
    """
    filename = path.stem
    relative_path = path.relative_to(directory)
    keys = ["procedures"] + list(relative_path.parts[:-1]) + [filename]

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
    return str(Path("procedures") / proc_config["path"] / file_name)


def get_file_contents(fpath: str, extra_context: dict[str, Any]) -> dict[str, Any]:
    """Load and render a file with ABSQL, including frontmatter parsing.

    Args:
        fpath: Path to the file to render
        extra_context: Additional context variables for template rendering

    Returns:
        Dictionary containing rendered content and metadata
    """
    return render_file(fpath, return_dict=True, extra_context=extra_context)  # type: ignore[no-any-return]


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
        str(Path(__file__).parent / "templates" / "javascript.sql"), **context
    )
    return {**kwargs, "rendered_file": rendered_file}


def grant_usage(proc: dict[str, Any], con: SnowflakeConnection) -> None:
    """Execute GRANT USAGE statements for a procedure.

    Grants procedure usage permissions to specified roles and users.
    Uses proper identifier quoting to prevent SQL injection.

    Args:
        proc: Procedure dictionary containing 'grant_usage', 'database', 'schema', 'name', 'args'
        con: Snowflake connection object
    """
    types = [arg["type"] for arg in proc["args"]]
    types_str = f"({','.join(types)})"

    database = quote_identifier(proc['database'])
    schema = quote_identifier(proc['schema'])
    proc_name = quote_identifier(proc['name'])

    for grantee_type in proc["grant_usage"]:
        grantee_type_upper = grantee_type.upper()
        for grantee in proc["grant_usage"][grantee_type]:
            grantee_quoted = quote_identifier(grantee)
            query = f"GRANT USAGE ON PROCEDURE {database}.{schema}.{proc_name}{types_str} TO {grantee_type_upper} {grantee_quoted}"
            con.cursor().execute(query)
