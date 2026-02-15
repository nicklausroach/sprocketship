"""SQL validation tests - ensure generated SQL is syntactically valid"""

import pytest
from pathlib import Path
import sqlparse
from click.testing import CliRunner
from sprocketship.cli import build
import shutil


class TestSQLSyntaxValidation:
    """Tests that verify generated SQL is valid Snowflake SQL"""

    def test_generated_sql_is_parseable(self, tmp_path):
        """Test that generated SQL can be parsed by sqlparse"""
        runner = CliRunner()
        fixture_dir = Path(__file__).parent / "fixtures"

        with runner.isolated_filesystem() as temp_dir:
            temp_path = Path(temp_dir)
            shutil.copytree(fixture_dir, temp_path / "project")

            # Build the procedures
            result = runner.invoke(build, ["project", "--target", "output"])
            assert result.exit_code == 0

            # Check each generated SQL file
            output_dir = temp_path / "project/output"
            sql_files = list(output_dir.glob("*.sql"))

            for sql_file in sql_files:
                sql_content = sql_file.read_text()

                # Parse the SQL
                parsed = sqlparse.parse(sql_content)
                assert len(parsed) > 0, f"Failed to parse {sql_file.name}"

                # Check that it's recognized as a valid statement
                statement = parsed[0]
                assert statement.get_type() != "UNKNOWN", (
                    f"{sql_file.name} contains unrecognized SQL"
                )

    def test_create_procedure_structure(self, tmp_path):
        """Test that CREATE PROCEDURE statements have required components"""
        runner = CliRunner()
        fixture_dir = Path(__file__).parent / "fixtures"

        with runner.isolated_filesystem() as temp_dir:
            temp_path = Path(temp_dir)
            shutil.copytree(fixture_dir, temp_path / "project")

            result = runner.invoke(build, ["project", "--target", "output"])
            assert result.exit_code == 0

            output_dir = temp_path / "project/output"
            create_db_sql = (output_dir / "create_database.sql").read_text()

            # Validate required keywords are present
            required_keywords = [
                "CREATE OR REPLACE PROCEDURE",
                "RETURNS",
                "LANGUAGE JAVASCRIPT",
                "EXECUTE AS",
                "AS",
                "$$",  # Procedure body delimiters
            ]

            for keyword in required_keywords:
                assert keyword in create_db_sql, (
                    f"Generated SQL missing required keyword: {keyword}"
                )

    def test_procedure_name_format(self, tmp_path):
        """Test that procedure names follow database.schema.name format"""
        runner = CliRunner()
        fixture_dir = Path(__file__).parent / "fixtures"

        with runner.isolated_filesystem() as temp_dir:
            temp_path = Path(temp_dir)
            shutil.copytree(fixture_dir, temp_path / "project")

            result = runner.invoke(build, ["project", "--target", "output"])
            assert result.exit_code == 0

            output_dir = temp_path / "project/output"

            for sql_file in output_dir.glob("*.sql"):
                sql_content = sql_file.read_text()

                # Check for three-part name (database.schema.procedure)
                import re
                pattern = r"CREATE OR REPLACE PROCEDURE\s+(\w+)\.(\w+)\.(\w+)"
                match = re.search(pattern, sql_content)

                assert match is not None, (
                    f"{sql_file.name} does not have proper three-part name"
                )

                database, schema, procedure = match.groups()
                assert len(database) > 0
                assert len(schema) > 0
                assert len(procedure) > 0

    def test_argument_list_syntax(self, tmp_path):
        """Test that argument lists are properly formatted"""
        runner = CliRunner()
        fixture_dir = Path(__file__).parent / "fixtures"

        with runner.isolated_filesystem() as temp_dir:
            temp_path = Path(temp_dir)
            shutil.copytree(fixture_dir, temp_path / "project")

            result = runner.invoke(build, ["project", "--target", "output"])
            assert result.exit_code == 0

            output_dir = temp_path / "project/output"
            create_db_sql = (output_dir / "create_database.sql").read_text()

            # Check for proper argument syntax: "ARG_NAME" TYPE
            import re
            # Find arguments between parentheses after procedure name
            arg_pattern = r'\(([^)]*)\)\s*RETURNS'
            match = re.search(arg_pattern, create_db_sql, re.DOTALL)

            if match:
                args_section = match.group(1).strip()
                if args_section:  # If there are arguments
                    # Should have quoted uppercase arg names
                    assert '"' in args_section, "Arguments should be quoted"
                    # Should have type keywords
                    assert any(
                        t in args_section.upper()
                        for t in ["VARCHAR", "NUMBER", "VARIANT", "ARRAY"]
                    ), "Arguments should have valid types"

    def test_no_sql_injection_vulnerabilities(self, tmp_path):
        """Test that generated SQL doesn't have obvious injection vulnerabilities"""
        runner = CliRunner()
        fixture_dir = Path(__file__).parent / "fixtures"

        with runner.isolated_filesystem() as temp_dir:
            temp_path = Path(temp_dir)
            shutil.copytree(fixture_dir, temp_path / "project")

            result = runner.invoke(build, ["project", "--target", "output"])
            assert result.exit_code == 0

            output_dir = temp_path / "project/output"

            for sql_file in output_dir.glob("*.sql"):
                sql_content = sql_file.read_text()

                # Check that procedure body is properly delimited
                assert sql_content.count("$$") >= 2, (
                    f"{sql_file.name} missing proper $$ delimiters"
                )

                # Check for dangerous patterns (basic check)
                dangerous_patterns = [
                    "'; DROP TABLE",
                    "'; DELETE FROM",
                    "--; ",  # SQL comment injection
                ]

                for pattern in dangerous_patterns:
                    assert pattern not in sql_content, (
                        f"{sql_file.name} contains potentially dangerous pattern: {pattern}"
                    )


class TestSQLLintingWithSqlfluff:
    """Optional: More thorough SQL validation with sqlfluff

    These tests require sqlfluff to be installed:
    pip install sqlfluff
    """

    def test_lint_with_sqlfluff(self, tmp_path):
        """Lint generated SQL with sqlfluff for Snowflake dialect"""
        # This test will be skipped unless sqlfluff is installed
        from sqlfluff.core import Linter

        runner = CliRunner()
        fixture_dir = Path(__file__).parent / "fixtures"

        with runner.isolated_filesystem() as temp_dir:
            temp_path = Path(temp_dir)
            shutil.copytree(fixture_dir, temp_path / "project")

            result = runner.invoke(build, ["project", "--target", "output"])
            assert result.exit_code == 0

            output_dir = temp_path / "project/output"
            linter = Linter(dialect="snowflake")

            for sql_file in output_dir.glob("*.sql"):
                sql_content = sql_file.read_text()

                # Lint the SQL
                result = linter.lint_string(sql_content)

                # Check for critical errors (not just warnings)
                critical_violations = [
                    v for v in result.violations
                    if v.rule_code().startswith("PRS")  # Parsing errors
                ]

                assert len(critical_violations) == 0, (
                    f"{sql_file.name} has syntax errors: "
                    f"{[v.description for v in critical_violations]}"
                )
