# Python tooling and software supply chain

## Status

`EXPERIMENTAL`

## Implemented controls

- Python minor line pinned through `.python-version` and `requires-python`.
- Direct development tools pinned to exact versions in `requirements-dev.lock`.
- Central Ruff, mypy, pytest, coverage and Bandit policy in `pyproject.toml`.
- Local pre-commit hooks without remote hook repositories.
- GitHub Actions with read-only contents permission, timeout and concurrency cancellation.
- External Actions referenced by immutable 40-character commit SHA.
- Dependency vulnerability scanning with `pip-audit`.
- Static security scanning with Bandit.

## Known limitation

`requirements-dev.lock` pins direct tools but does not yet contain hashes or a complete transitive resolution. It must not be represented as a hermetic supply-chain lock. Promotion beyond `EXPERIMENTAL` requires generating and reviewing a platform-compatible lock with hashes from a trusted, network-enabled build environment.

## Local verification

```bash
python -m pip install -r requirements-dev.lock
python -m ruff check .
python -m ruff format --check .
python -m mypy repo_agent_platform
python -m pytest
python -m bandit -c pyproject.toml -r repo_agent_platform
python -m pip_audit -r requirements-dev.lock --strict
pre-commit run --all-files
```

## Rollback

Revert the PR that introduced these files. No database migration, deployment, secret rotation or production state change is involved.
