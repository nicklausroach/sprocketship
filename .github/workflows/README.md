# GitHub Actions Workflows

## Active Workflows

### `test.yml` - Continuous Testing
**Triggers:** Push to `main`/`develop`, Pull Requests
**Purpose:** Run full test suite on every change

**What it does:**
1. **Test Matrix** - Tests on Python 3.9, 3.10, 3.11, 3.12
2. **Coverage Report** - Uploads coverage to Codecov
3. **Coverage Threshold** - Fails if coverage drops below 80%
4. **SQL Validation** - Validates generated SQL syntax
5. **Integration Test** - Tests build command end-to-end

**Jobs:**
- `test` - Run pytest on multiple Python versions
- `lint` - SQL validation and linting
- `integration` - Test CLI commands work end-to-end
- `status-check` - Combined status for branch protection

### `publish-to-pypi.yml` - Package Publishing
**Triggers:** Push to tags (`refs/tags/*`)
**Purpose:** Publish package to PyPI on releases

**What it does:**
1. Build distribution packages
2. Publish to PyPI using trusted publishing
3. Sign with Sigstore
4. Create GitHub Release

### `claude.yml` - Claude PR Assistant
**Triggers:** Pull request events
**Purpose:** AI-powered PR assistance

### `claude-code-review.yml` - Claude Code Review
**Triggers:** Pull request events
**Purpose:** Automated code review

## Adding Status Badges

Add these to your README.md:

```markdown
[![Tests](https://github.com/nicklausroach/sprocketship/actions/workflows/test.yml/badge.svg)](https://github.com/nicklausroach/sprocketship/actions/workflows/test.yml)
[![PyPI](https://img.shields.io/pypi/v/sprocketship)](https://pypi.org/project/sprocketship/)
[![Python Version](https://img.shields.io/pypi/pyversions/sprocketship)](https://pypi.org/project/sprocketship/)
[![Coverage](https://codecov.io/gh/nicklausroach/sprocketship/branch/main/graph/badge.svg)](https://codecov.io/gh/nicklausroach/sprocketship)
```

## Branch Protection Setup

Recommended branch protection rules for `main`:

1. **Require status checks to pass:**
   - `All tests passed` (from test.yml)

2. **Require pull request reviews:**
   - At least 1 approval

3. **Require branches to be up to date before merging**

### Setup Instructions

1. Go to: Settings → Branches → Branch protection rules
2. Add rule for `main` branch
3. Enable "Require status checks to pass before merging"
4. Select "All tests passed" from the status checks list
5. Enable "Require branches to be up to date before merging"

## Local Testing

Run the same checks locally before pushing:

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests (like CI does)
pytest -v --cov=sprocketship --cov-report=term-missing

# SQL validation only
pytest tests/test_sql_validation.py -v

# Integration test
sprocketship build tests/fixtures --target /tmp/test
```

## Workflow Tips

### Skip CI on commits
Add `[skip ci]` or `[ci skip]` to commit message:
```bash
git commit -m "Update docs [skip ci]"
```

### Re-run failed jobs
1. Go to Actions tab
2. Click on failed workflow run
3. Click "Re-run failed jobs"

### View detailed logs
1. Go to Actions tab
2. Click on workflow run
3. Click on specific job
4. Expand step to see full logs

## Troubleshooting

### Tests pass locally but fail in CI
- Check Python version (CI tests on 3.9-3.12)
- Check dependencies are installed correctly
- Look for OS-specific issues (CI uses Ubuntu)

### Coverage threshold failure
- Run `pytest --cov=sprocketship --cov-report=html` locally
- Open `htmlcov/index.html` to see what's not covered
- Add tests or adjust threshold in `test.yml`

### Integration test failures
- Verify fixtures are committed
- Check file paths are relative, not absolute
- Ensure no Snowflake credentials are required
