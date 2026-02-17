"""Integration tests for CLI commands"""

import pytest
from pathlib import Path
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from sprocketship.cli import build, liftoff
import shutil


@pytest.fixture
def cli_runner():
    """Fixture for Click CLI runner"""
    return CliRunner()


@pytest.fixture
def fixture_dir():
    """Fixture for test fixtures directory"""
    return Path(__file__).parent / "fixtures"


class TestBuildCommand:
    """Tests for the build command - no Snowflake required!"""

    def test_build_with_fixtures(self, cli_runner, fixture_dir):
        """Test build command with test fixtures"""
        with cli_runner.isolated_filesystem() as temp_dir:
            temp_path = Path(temp_dir)

            # Copy fixtures to temp directory
            shutil.copytree(fixture_dir, temp_path / "project")

            # Run build command
            result = cli_runner.invoke(build, ["project", "--target", "output"])

            # Check exit code
            assert result.exit_code == 0, f"Build failed: {result.output}"

            # Verify output files were created
            output_dir = temp_path / "project/output"
            assert output_dir.exists()

            # Check that SQL files were generated
            sql_files = list(output_dir.glob("*.sql"))
            assert len(sql_files) == 3  # create_database, drop_database, create_user

            # Verify SQL content
            create_db_sql = (output_dir / "create_database.sql").read_text()
            assert "CREATE OR REPLACE PROCEDURE" in create_db_sql
            assert "admin_db.default_schema.create_database" in create_db_sql
            # Arguments are quoted and uppercase in actual template
            assert '"DATABASE_NAME" VARCHAR' in create_db_sql

    def test_build_default_target(self, cli_runner, fixture_dir):
        """Test build command with default target directory"""
        with cli_runner.isolated_filesystem() as temp_dir:
            temp_path = Path(temp_dir)
            shutil.copytree(fixture_dir, temp_path / "project")

            result = cli_runner.invoke(build, ["project"])

            assert result.exit_code == 0
            # Should create default target/sprocketship directory
            default_output = temp_path / "project/target/sprocketship"
            assert default_output.exists()
            assert len(list(default_output.glob("*.sql"))) > 0

    def test_build_missing_config(self, cli_runner):
        """Test build command fails gracefully with missing config"""
        with cli_runner.isolated_filesystem():
            Path("procedures").mkdir()
            Path("procedures/test.js").write_text("return 'hello';")

            result = cli_runner.invoke(build, ["."])

            assert result.exit_code == 1
            assert "Configuration file not found" in result.output

    def test_build_invalid_yaml(self, cli_runner):
        """Test build command fails gracefully with invalid YAML"""
        with cli_runner.isolated_filesystem():
            Path(".sprocketship.yml").write_text("invalid: yaml: content:")

            result = cli_runner.invoke(build, ["."])

            assert result.exit_code == 1
            assert "Failed to load configuration" in result.output

    def test_build_verify_config_merging(self, cli_runner, fixture_dir):
        """Test that build correctly merges hierarchical configs"""
        with cli_runner.isolated_filesystem() as temp_dir:
            temp_path = Path(temp_dir)
            shutil.copytree(fixture_dir, temp_path / "project")

            cli_runner.invoke(build, ["project", "--target", "output"])

            # Check create_user procedure got correct config
            create_user_sql = (temp_path / "project/output/create_user.sql").read_text()

            # Should use default_database (from root +database)
            assert "default_database" in create_user_sql
            # Should use user_schema (from useradmin +schema)
            assert "user_schema" in create_user_sql

    def test_build_with_frontmatter_override(self, cli_runner, fixture_dir):
        """Test that frontmatter overrides YAML config"""
        with cli_runner.isolated_filesystem() as temp_dir:
            temp_path = Path(temp_dir)
            shutil.copytree(fixture_dir, temp_path / "project")

            cli_runner.invoke(build, ["project", "--target", "output"])

            # drop_database has frontmatter comment override
            drop_db_sql = (temp_path / "project/output/drop_database.sql").read_text()
            assert "Drops a database - overriding config in frontmatter" in drop_db_sql

    def test_build_only_single_procedure(self, cli_runner, fixture_dir):
        """Test build command with --only flag for single procedure"""
        with cli_runner.isolated_filesystem() as temp_dir:
            temp_path = Path(temp_dir)
            shutil.copytree(fixture_dir, temp_path / "project")

            result = cli_runner.invoke(build, ["project", "--target", "output", "--only", "create_database"])

            assert result.exit_code == 0
            output_dir = temp_path / "project/output"

            # Should only build create_database, not all 3 procedures
            sql_files = list(output_dir.glob("*.sql"))
            assert len(sql_files) == 1
            assert (output_dir / "create_database.sql").exists()
            assert not (output_dir / "drop_database.sql").exists()
            assert not (output_dir / "create_user.sql").exists()

    def test_build_only_multiple_procedures(self, cli_runner, fixture_dir):
        """Test build command with multiple --only flags"""
        with cli_runner.isolated_filesystem() as temp_dir:
            temp_path = Path(temp_dir)
            shutil.copytree(fixture_dir, temp_path / "project")

            result = cli_runner.invoke(
                build,
                ["project", "--target", "output", "--only", "create_database", "--only", "drop_database"]
            )

            assert result.exit_code == 0
            output_dir = temp_path / "project/output"

            # Should only build the two specified procedures
            sql_files = list(output_dir.glob("*.sql"))
            assert len(sql_files) == 2
            assert (output_dir / "create_database.sql").exists()
            assert (output_dir / "drop_database.sql").exists()
            assert not (output_dir / "create_user.sql").exists()

    def test_build_only_nonexistent_procedure(self, cli_runner, fixture_dir):
        """Test build command warns when --only specifies nonexistent procedure"""
        with cli_runner.isolated_filesystem() as temp_dir:
            temp_path = Path(temp_dir)
            shutil.copytree(fixture_dir, temp_path / "project")

            result = cli_runner.invoke(
                build,
                ["project", "--target", "output", "--only", "nonexistent"]
            )

            assert result.exit_code == 0  # Should succeed but with warning
            assert "Could not find procedure(s): nonexistent" in result.output

            # Should not build any procedures
            output_dir = temp_path / "project/output"
            sql_files = list(output_dir.glob("*.sql"))
            assert len(sql_files) == 0


class TestLiftoffCommand:
    """Tests for the liftoff command - mocking Snowflake connection"""

    @patch("sprocketship.cli.connector.connect")
    def test_liftoff_with_mock_snowflake(self, mock_connect, cli_runner, fixture_dir):
        """Test liftoff command with mocked Snowflake connection"""
        # Setup mock connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        with cli_runner.isolated_filesystem() as temp_dir:
            temp_path = Path(temp_dir)
            shutil.copytree(fixture_dir, temp_path / "project")

            result = cli_runner.invoke(liftoff, ["project"])

            # Should succeed
            assert result.exit_code == 0
            assert "Sprocketship lifting off!" in result.output
            assert "launched into schema" in result.output

            # Verify Snowflake connection was established
            mock_connect.assert_called_once()
            connect_args = mock_connect.call_args[1]
            assert connect_args["account"] == "test_account"
            assert connect_args["user"] == "test_user"
            assert connect_args["role"] == "sysadmin"

            # Verify CREATE PROCEDURE was executed
            assert mock_cursor.execute.called
            # Should have executed USE ROLE and CREATE PROCEDURE for each file
            calls = [str(call) for call in mock_cursor.execute.call_args_list]
            assert any("USE ROLE" in str(call) for call in calls)
            assert any("CREATE OR REPLACE PROCEDURE" in str(call) for call in calls)

    @patch("sprocketship.cli.connector.connect")
    def test_liftoff_role_switching(self, mock_connect, cli_runner, fixture_dir):
        """Test that liftoff switches roles correctly based on use_role config"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        with cli_runner.isolated_filesystem() as temp_dir:
            temp_path = Path(temp_dir)
            shutil.copytree(fixture_dir, temp_path / "project")

            cli_runner.invoke(liftoff, ["project"])

            # Check that role switching happened
            execute_calls = [call[0][0] for call in mock_cursor.execute.call_args_list]

            # Should have USE ROLE "SYSADMIN" for admin procedures (quoted for SQL injection prevention)
            assert any('USE ROLE "SYSADMIN"' in call for call in execute_calls)
            # Should have USE ROLE "USERADMIN" for useradmin procedures
            assert any('USE ROLE "USERADMIN"' in call for call in execute_calls)

    @patch("sprocketship.cli.connector.connect")
    def test_liftoff_with_grant_usage(self, mock_connect, cli_runner, fixture_dir):
        """Test that liftoff executes GRANT USAGE statements"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        with cli_runner.isolated_filesystem() as temp_dir:
            temp_path = Path(temp_dir)
            shutil.copytree(fixture_dir, temp_path / "project")

            cli_runner.invoke(liftoff, ["project"])

            # Check that GRANT statements were executed
            execute_calls = [call[0][0] for call in mock_cursor.execute.call_args_list]
            grant_calls = [call for call in execute_calls if "GRANT USAGE" in call]

            # create_user has grant_usage config, so should have grant statements
            assert len(grant_calls) > 0
            assert any("GRANT USAGE ON PROCEDURE" in call for call in grant_calls)
            # Identifiers are now quoted for SQL injection prevention
            assert any('TO ROLE "analyst"' in call for call in grant_calls)

    @patch("sprocketship.cli.connector.connect")
    def test_liftoff_show_flag(self, mock_connect, cli_runner, fixture_dir):
        """Test that --show flag displays SQL"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        with cli_runner.isolated_filesystem() as temp_dir:
            temp_path = Path(temp_dir)
            shutil.copytree(fixture_dir, temp_path / "project")

            result = cli_runner.invoke(liftoff, ["project", "--show"])

            # Should show the SQL in output
            assert "CREATE OR REPLACE PROCEDURE" in result.output

    def test_liftoff_missing_snowflake_config(self, cli_runner):
        """Test liftoff fails gracefully with missing snowflake config"""
        with cli_runner.isolated_filesystem():
            Path(".sprocketship.yml").write_text("""
procedures:
  +database: test_db
""")
            Path("procedures").mkdir()
            Path("procedures/test.js").write_text("return 'hello';")

            result = cli_runner.invoke(liftoff, ["."])

            assert result.exit_code == 1
            assert "Missing 'snowflake' section" in result.output

    @patch("sprocketship.cli.connector.connect")
    def test_liftoff_connection_failure(self, mock_connect, cli_runner, fixture_dir):
        """Test liftoff handles connection failures gracefully"""
        mock_connect.side_effect = Exception("Connection failed")

        with cli_runner.isolated_filesystem() as temp_dir:
            temp_path = Path(temp_dir)
            shutil.copytree(fixture_dir, temp_path / "project")

            result = cli_runner.invoke(liftoff, ["project"])

            assert result.exit_code == 1
            assert "Failed to connect to Snowflake" in result.output

    @patch("sprocketship.cli.connector.connect")
    def test_liftoff_continues_on_procedure_error(self, mock_connect, cli_runner, fixture_dir):
        """Test that liftoff continues processing if one procedure fails"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        # First procedure succeeds, second fails, third succeeds
        mock_cursor.execute.side_effect = [
            None,  # USE ROLE
            None,  # CREATE PROCEDURE (success)
            None,  # USE ROLE
            Exception("SQL error"),  # CREATE PROCEDURE (fail)
            None,  # USE ROLE
            None,  # CREATE PROCEDURE (success)
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        with cli_runner.isolated_filesystem() as temp_dir:
            temp_path = Path(temp_dir)
            shutil.copytree(fixture_dir, temp_path / "project")

            result = cli_runner.invoke(liftoff, ["project"])

            # Should exit with error but show some successes
            assert result.exit_code == 1
            assert "could not be launched" in result.output
            # At least one should have succeeded
            assert "launched into schema" in result.output

    @patch("sprocketship.cli.connector.connect")
    def test_liftoff_only_single_procedure(self, mock_connect, cli_runner, fixture_dir):
        """Test liftoff command with --only flag for single procedure"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        with cli_runner.isolated_filesystem() as temp_dir:
            temp_path = Path(temp_dir)
            shutil.copytree(fixture_dir, temp_path / "project")

            result = cli_runner.invoke(liftoff, ["project", "--only", "create_database"])

            assert result.exit_code == 0

            # Should only execute CREATE PROCEDURE once (plus USE ROLE)
            execute_calls = [call[0][0] for call in mock_cursor.execute.call_args_list]
            create_calls = [call for call in execute_calls if "CREATE OR REPLACE PROCEDURE" in call]

            # Should only deploy create_database, not all 3 procedures
            assert len(create_calls) == 1
            assert "create_database" in create_calls[0]

    @patch("sprocketship.cli.connector.connect")
    def test_liftoff_only_multiple_procedures(self, mock_connect, cli_runner, fixture_dir):
        """Test liftoff command with multiple --only flags"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        with cli_runner.isolated_filesystem() as temp_dir:
            temp_path = Path(temp_dir)
            shutil.copytree(fixture_dir, temp_path / "project")

            result = cli_runner.invoke(
                liftoff,
                ["project", "--only", "create_database", "--only", "drop_database"]
            )

            assert result.exit_code == 0

            # Should execute CREATE PROCEDURE twice (plus USE ROLE calls)
            execute_calls = [call[0][0] for call in mock_cursor.execute.call_args_list]
            create_calls = [call for call in execute_calls if "CREATE OR REPLACE PROCEDURE" in call]

            # Should only deploy the two specified procedures
            assert len(create_calls) == 2
            assert any("create_database" in call for call in create_calls)
            assert any("drop_database" in call for call in create_calls)

    @patch("sprocketship.cli.connector.connect")
    def test_liftoff_only_nonexistent_procedure(self, mock_connect, cli_runner, fixture_dir):
        """Test liftoff command warns when --only specifies nonexistent procedure"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        with cli_runner.isolated_filesystem() as temp_dir:
            temp_path = Path(temp_dir)
            shutil.copytree(fixture_dir, temp_path / "project")

            result = cli_runner.invoke(liftoff, ["project", "--only", "nonexistent"])

            assert result.exit_code == 0  # Should succeed but with warning
            assert "Could not find procedure(s): nonexistent" in result.output

            # Should not execute any CREATE PROCEDURE statements
            execute_calls = [call[0][0] for call in mock_cursor.execute.call_args_list]
            create_calls = [call for call in execute_calls if "CREATE OR REPLACE PROCEDURE" in call]
            assert len(create_calls) == 0

    @patch("sprocketship.cli.connector.connect")
    def test_liftoff_dry_run(self, mock_connect, cli_runner, fixture_dir):
        """Test liftoff --dry-run previews SQL without connecting to Snowflake"""
        with cli_runner.isolated_filesystem() as temp_dir:
            temp_path = Path(temp_dir)
            shutil.copytree(fixture_dir, temp_path / "project")

            result = cli_runner.invoke(liftoff, ["project", "--dry-run"])

            # Should succeed
            assert result.exit_code == 0

            # Should show dry-run mode message
            assert "dry-run mode" in result.output
            assert "preview only" in result.output

            # Should NOT connect to Snowflake in dry-run mode
            mock_connect.assert_not_called()

            # Should show SQL in output
            assert "CREATE OR REPLACE PROCEDURE" in result.output

            # Should show what would be deployed
            assert "would be deployed to" in result.output
            assert "admin_db.default_schema" in result.output

            # Should show role information
            assert "using role" in result.output
            assert "SYSADMIN" in result.output or "USERADMIN" in result.output

    @patch("sprocketship.cli.connector.connect")
    def test_liftoff_dry_run_with_only(self, mock_connect, cli_runner, fixture_dir):
        """Test liftoff --dry-run with --only flag"""
        with cli_runner.isolated_filesystem() as temp_dir:
            temp_path = Path(temp_dir)
            shutil.copytree(fixture_dir, temp_path / "project")

            result = cli_runner.invoke(
                liftoff,
                ["project", "--dry-run", "--only", "create_database"]
            )

            assert result.exit_code == 0

            # Should NOT connect to Snowflake
            mock_connect.assert_not_called()

            # Should only show create_database, not other procedures
            assert "create_database" in result.output
            # Count occurrences of "would be deployed" - should only be 1
            assert result.output.count("would be deployed to") == 1

    @patch("sprocketship.cli.connector.connect")
    def test_liftoff_dry_run_shows_grant_usage(self, mock_connect, cli_runner, fixture_dir):
        """Test liftoff --dry-run shows grant_usage permissions"""
        with cli_runner.isolated_filesystem() as temp_dir:
            temp_path = Path(temp_dir)
            shutil.copytree(fixture_dir, temp_path / "project")

            result = cli_runner.invoke(
                liftoff,
                ["project", "--dry-run", "--only", "create_user"]
            )

            assert result.exit_code == 0

            # Should NOT connect to Snowflake
            mock_connect.assert_not_called()

            # Should show grant usage information
            assert "Would grant usage to:" in result.output
            # The create_user fixture has grant_usage for role: analyst
            assert "role:" in result.output
            assert "analyst" in result.output
