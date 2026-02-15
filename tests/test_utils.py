"""Unit tests for sprocketship.utils module"""

import pytest
from pathlib import Path
from sprocketship.utils import (
    extract_configs,
    get_file_config,
    create_javascript_stored_procedure,
)


class TestExtractConfigs:
    """Tests for extract_configs function

    This function appears to be for extracting flat config paths from nested structures.
    It's imported but not actively used in the main CLI code.
    """

    def test_path_assignment(self):
        """Test that paths are assigned correctly to list items"""
        data = {
            "test_proc": [{"name": "config1"}, {"name": "config2"}]
        }
        result = extract_configs(data)
        assert "test_proc" in result
        configs = result["test_proc"]
        assert configs[0]["path"] == "test_proc"
        assert configs[1]["path"] == "test_proc"


class TestGetFileConfig:
    """Tests for get_file_config function - the core config merging logic

    This function builds keys as: ["procedures"] + directory_parts + [filename]
    and walks through the config dict applying + prefixed (cascading) configs at each level.
    """

    def test_with_real_fixture_structure(self):
        """Test with actual fixture structure"""
        from absql import render_file

        fixture_dir = Path(__file__).parent / "fixtures"
        config_path = fixture_dir / ".sprocketship.yml"
        data = render_file(str(config_path), return_dict=True)

        # Test admin/create_database.js
        file_path = fixture_dir / "admin/create_database.js"
        result = get_file_config(file_path, data, str(fixture_dir))

        assert result["name"] == "create_database"
        assert result["database"] == "admin_db"  # From admin +database
        assert result["schema"] == "default_schema"  # From procedures +schema
        assert result["use_role"] == "sysadmin"  # From admin +use_role
        assert result["args"] == [{"name": "database_name", "type": "varchar"}]
        assert result["returns"] == "varchar"

    def test_missing_intermediate_keys(self):
        """Test that missing intermediate keys don't cause errors"""
        config = {
            "procedures": {
                "+database": "default_db",
            }
        }
        path = Path("missing/test_proc.js")
        result = get_file_config(path, config, ".")

        # Should still get the cascading values
        assert result["database"] == "default_db"
        assert result["name"] == "test_proc"

    def test_path_stored_in_result(self):
        """Test that file path is stored in result"""
        config = {"procedures": {}}
        path = Path("test.js")
        result = get_file_config(path, config, ".")

        assert "path" in result
        assert "test.js" in result["path"]


class TestCreateJavascriptStoredProcedure:
    """Tests for create_javascript_stored_procedure function"""

    def test_procedure_creation_with_fixtures(self, tmp_path):
        """Test SQL generation with actual fixture files"""
        fixture_dir = Path(__file__).parent / "fixtures"
        proc_path = fixture_dir / "admin/create_database.js"

        # Minimal config needed for rendering
        config = {
            "path": str(proc_path),
            "name": "create_database",
            "database": "test_db",
            "schema": "test_schema",
            "language": "javascript",
            "execute_as": "owner",
            "args": [{"name": "database_name", "type": "varchar"}],
            "returns": "varchar",
            "comment": "Creates a database",
        }

        result = create_javascript_stored_procedure(**config)

        # Verify structure
        assert "rendered_file" in result
        assert "CREATE OR REPLACE PROCEDURE" in result["rendered_file"]
        assert "test_db.test_schema.create_database" in result["rendered_file"]
        # Arguments are quoted and uppercase in the template
        assert '"DATABASE_NAME" VARCHAR' in result["rendered_file"]
        assert "RETURNS varchar" in result["rendered_file"]
        assert "var databaseName = DATABASE_NAME" in result["rendered_file"]

    def test_procedure_with_multiple_args(self, tmp_path):
        """Test SQL generation with multiple arguments"""
        # Create a temporary procedure file
        proc_file = tmp_path / "test_proc.js"
        proc_file.write_text("return ARG1 + ARG2;")

        config = {
            "path": str(proc_file),
            "name": "test_proc",
            "database": "test_db",
            "schema": "test_schema",
            "language": "javascript",
            "execute_as": "caller",
            "args": [
                {"name": "arg1", "type": "varchar"},
                {"name": "arg2", "type": "number"},
            ],
            "returns": "number",
        }

        result = create_javascript_stored_procedure(**config)

        # Arguments are quoted and uppercase, with space before comma
        assert '"ARG1" VARCHAR' in result["rendered_file"]
        assert '"ARG2" NUMBER' in result["rendered_file"]
        assert "EXECUTE AS caller" in result["rendered_file"]

    def test_procedure_with_comment(self, tmp_path):
        """Test that comments are included in generated SQL"""
        proc_file = tmp_path / "test_proc.js"
        proc_file.write_text("return 'hello';")

        config = {
            "path": str(proc_file),
            "name": "test_proc",
            "database": "test_db",
            "schema": "test_schema",
            "language": "javascript",
            "execute_as": "owner",
            "args": [],
            "returns": "varchar",
            "comment": "This is a test procedure\nwith multiple lines",
        }

        result = create_javascript_stored_procedure(**config)

        # Comments use single quotes not $$
        assert "COMMENT = '" in result["rendered_file"]
        assert "This is a test procedure" in result["rendered_file"]
        assert "with multiple lines" in result["rendered_file"]
