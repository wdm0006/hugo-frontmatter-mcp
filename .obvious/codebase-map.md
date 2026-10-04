# Codebase Map — wdm0006/hugo-frontmatter-mcp

Depth-capped at 2. Single-module Python MCP server (stdio) for Hugo frontmatter operations.

| Path | Kind | Purpose |
|---|---|---|
| `hugo_frontmatter_mcp.py` | module (531 lines) | Entire MCP server: `FastMCP("HugoFrontmatterMCP")` instance, `_load_post` / `_save_post` helpers, 15 `@mcp_server.tool()` functions — single-file ops (`get_frontmatter`, `get_field`, `set_title`, `set_date`, `set_publish_date`, `set_description`, `set_draft_status`, `add_tag`, `remove_tag`, `add_image`, `remove_image`) and directory batch ops (`list_tags_in_directory`, `find_posts_by_tag`, `rename_tag_in_directory`, `validate_date_formats`) — plus `main()` stdio entry point |
| `tests/` | dir | Test suite |
| `tests/test_frontmatter_api.py` | test (589 lines) | 44 pytest tests: every tool, error paths (relative path, missing file, wrong types), key-order preservation, symlink skipping, startup message on stderr |
| `.github/` | dir | CI config |
| `.github/workflows/ci.yml` | workflow | `lint` job (ruff check + format check, Py 3.12); `test` job (pytest on Py 3.10/3.11/3.12); both use uv with cache |
| `pyproject.toml` | manifest | hatchling build; deps fastmcp>=3.4.5,<4.0.0, python-frontmatter, pyyaml; dev extras ruff/pytest/pre-commit; `hugo-frontmatter-mcp` script entry; ruff config (line-length 120) |
| `uv.lock` | lockfile | uv lock, pins fastmcp 3.4.5 |
| `Makefile` | build | `install` / `lint` / `lint-check` / `format` / `format-check` / `test` / `clean` — note every target depends on `install`, which recreates `.venv` (use `UV_VENV_CLEAR=1` or direct uv commands) |
| `Dockerfile` | image | `python:3.10-slim`, installs the package, `CMD ["python3", "hugo_frontmatter_mcp.py"]` (Smithery-generated) |
| `smithery.yaml` | deploy | Smithery stdio start command (`python3 hugo_frontmatter_mcp.py`), empty config schema |
| `.pre-commit-config.yaml` | hooks | trailing-whitespace, end-of-file-fixer, check-yaml, large-files; ruff + ruff-format (v0.9.7) |
| `README.md` | docs | Features, install (uvx / uv sync / Smithery), MCP client config JSON, full tool API list |
| `LICENSE` | docs | MIT |
| `.gitignore` | config | standard Python ignores; `.venv`, `.env` ignored; `.obvious/` is NOT ignored |
