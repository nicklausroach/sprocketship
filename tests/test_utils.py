"""Unit tests for sprocketship.utils module"""

import pytest
from pathlib import Path
from sprocketship.utils import (
    ConfigurationError,
    filter_procedures,
    get_file_config,
    create_javascript_stored_procedure,
    validate_procedure_config,
)


class TestFilterProcedures:
    """Tests for filter_procedures function"""

    def test_no_filter_returns_all_files(self):
        """Test that empty filter returns all files"""
        files = [Path("proc1.js"), Path("proc2.js"), Path("proc3.js")]
        filtered, not_found = filter_procedures(files, tuple())

        assert filtered == files
        assert not_found == set()

    def test_filter_single_procedure(self):
        """Test filtering for a single procedure"""
        files = [Path("proc1.js"), Path("proc2.js"), Path("proc3.js")]
        filtered, not_found = filter_procedures(files, ("proc2",))

        assert len(filtered) == 1
        assert filtered[0] == Path("proc2.js")
        assert not_found == set()

    def test_filter_multiple_procedures(self):
        """Test filtering for multiple procedures"""
        files = [Path("proc1.js"), Path("proc2.js"), Path("proc3.js")]
        filtered, not_found = filter_procedures(files, ("proc1", "proc3"))

        assert len(filtered) == 2
        assert Path("proc1.js") in filtered
        assert Path("proc3.js") in filtered
        assert Path("proc2.js") not in filtered
        assert not_found == set()

    def test_nonexistent_procedure_returns_not_found(self):
        """Test that nonexistent procedures are reported"""
        files = [Path("proc1.js"), Path("proc2.js")]
        filtered, not_found = filter_procedures(files, ("proc3",))

        assert len(filtered) == 0
        assert not_found == {"proc3"}

    def test_mixed_existing_and_nonexistent(self):
        """Test filtering with mix of existing and nonexistent procedures"""
        files = [Path("proc1.js"), Path("proc2.js")]
        filtered, not_found = filter_procedures(files, ("proc1", "proc3", "proc4"))

        assert len(filtered) == 1
        assert filtered[0] == Path("proc1.js")
        assert not_found == {"proc3", "proc4"}

    def test_nested_path_filters_by_stem(self):
        """Test that filtering works with nested paths using filename stem"""
        files = [
            Path("admin/create_db.js"),
            Path("useradmin/create_user.js"),
            Path("admin/drop_db.js"),
        ]
        filtered, not_found = filter_procedures(files, ("create_db", "create_user"))

        assert len(filtered) == 2
        assert Path("admin/create_db.js") in filtered
        assert Path("useradmin/create_user.js") in filtered
        assert not_found == set()


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


class TestValidateProcedureConfig:
    """Tests for validate_procedure_config function"""

    def test_valid_config_passes(self):
        """Test that a valid configuration passes validation"""
        config = {
            "database": "test_db",
            "schema": "test_schema",
            "returns": "varchar",
            "language": "javascript",
            "execute_as": "owner",
            "path": "test.js",
        }
        # Should not raise any exception
        validate_procedure_config(config, "test")

    def test_missing_database_raises_error(self):
        """Test that missing database field raises ConfigurationError"""
        config = {
            "schema": "test_schema",
            "returns": "varchar",
            "language": "javascript",
            "execute_as": "owner",
        }
        with pytest.raises(ConfigurationError) as exc_info:
            validate_procedure_config(config, "test")

        assert "[E002]" in str(exc_info.value)
        assert "database" in str(exc_info.value).lower()
        assert "Missing required configuration fields" in str(exc_info.value)

    def test_missing_multiple_fields_raises_error(self):
        """Test that missing multiple fields are all reported"""
        config = {
            "database": "test_db",
            # Missing: schema, returns, language, execute_as
        }
        with pytest.raises(ConfigurationError) as exc_info:
            validate_procedure_config(config, "test")

        error_msg = str(exc_info.value)
        assert "schema" in error_msg
        assert "returns" in error_msg
        assert "language" in error_msg
        assert "execute_as" in error_msg

    def test_invalid_language_raises_error(self):
        """Test that invalid language value raises ConfigurationError"""
        config = {
            "database": "test_db",
            "schema": "test_schema",
            "returns": "varchar",
            "language": "ruby",  # Invalid language
            "execute_as": "owner",
        }
        with pytest.raises(ConfigurationError) as exc_info:
            validate_procedure_config(config, "test")

        assert "[E003]" in str(exc_info.value)
        assert "Unsupported language" in str(exc_info.value)
        assert "ruby" in str(exc_info.value)

    def test_invalid_execute_as_raises_error(self):
        """Test that invalid execute_as value raises ConfigurationError"""
        config = {
            "database": "test_db",
            "schema": "test_schema",
            "returns": "varchar",
            "language": "javascript",
            "execute_as": "admin",  # Invalid execute_as
        }
        with pytest.raises(ConfigurationError) as exc_info:
            validate_procedure_config(config, "test")

        assert "[E003]" in str(exc_info.value)
        assert "Invalid execute_as value" in str(exc_info.value)
        assert "admin" in str(exc_info.value)

    def test_error_includes_fix_suggestions(self):
        """Test that errors include helpful fix suggestions"""
        config = {
            "database": "test_db",
            "schema": "test_schema",
            # Missing: returns, language, execute_as
        }
        with pytest.raises(ConfigurationError) as exc_info:
            validate_procedure_config(config, "test_proc")

        error_msg = str(exc_info.value)
        # Should suggest both frontmatter and YAML fixes
        assert "Fix option 1" in error_msg
        assert "Fix option 2" in error_msg
        assert "frontmatter" in error_msg.lower()
        assert ".sprocketship.yml" in error_msg

    def test_none_values_treated_as_missing(self):
        """Test that None values are treated as missing fields"""
        config = {
            "database": "test_db",
            "schema": None,  # None should be treated as missing
            "returns": "varchar",
            "language": "javascript",
            "execute_as": "owner",
        }
        with pytest.raises(ConfigurationError) as exc_info:
            validate_procedure_config(config, "test")

        assert "schema" in str(exc_info.value)


class TestConfigurationError:
    """Tests for ConfigurationError exception class"""

    def test_error_without_code(self):
        """Test ConfigurationError without error code"""
        error = ConfigurationError("Test error message")
        assert str(error) == "Test error message"
        assert error.error_code is None

    def test_error_with_code(self):
        """Test ConfigurationError with error code"""
        error = ConfigurationError("Test error message", error_code="E001")
        assert "[E001]" in str(error)
        assert "Test error message" in str(error)
        assert error.error_code == "E001"
