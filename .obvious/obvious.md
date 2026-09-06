# wdm0006/hugo-frontmatter-mcp — Agent Contract

Single-module Python MCP server (stdio transport) for reading, updating, and validating YAML frontmatter in Hugo Markdown files. No web server, no ports, no external services.

## Stack

| Layer | Value |
|---|---|
| Language | Python >= 3.10 (CI matrix: 3.10 / 3.11 / 3.12) |
| App type | MCP server over **stdio** — spawned per client session, no HTTP port, no daemon |
| Core deps | fastmcp 3.4.5, python-frontmatter, pyyaml |
| Dev deps | ruff (lint + format), pytest, pre-commit |
| Package manager | uv (`uv.lock` committed); installs via `uv pip install -e ".[dev]"` |
| External services | None — no database, no cache, no network at runtime |
| Required env vars | None |

## Commands

| Task | Command | Notes |
|---|---|---|
| Install (fresh checkout) | `make install` | `uv venv .venv --seed` + `uv pip install -e ".[dev]"`. **Fails if `.venv` already exists.** |
| Install (over existing venv) | `UV_VENV_CLEAR=1 make install` | clears and recreates `.venv` |
| Lint | `uv run ruff check .` | line-length 120; E501 and C901 ignored |
| Format check | `uv run ruff format --check .` | double quotes |
| Tests | `uv run pytest tests/ -v` | 44 tests, ~2s, no network needed |
| Run the server | `uv run hugo_frontmatter_mcp.py` | stdio MCP; prints `Starting Hugo Frontmatter MCP server. Expects absolute paths.` to stderr; runs until client disconnects |
| Run via entry point | `uv run hugo-frontmatter-mcp` | same server through `[project.scripts]` |
| Make targets | `make lint-check` / `make format-check` / `make test` | every target re-runs `install` — use `UV_VENV_CLEAR=1 make <target>` or the direct uv commands above |

**Makefile quirk:** `install` is a prerequisite of lint/format/test targets and unconditionally runs `uv venv .venv --seed`, which errors when `.venv` exists. CI (`.github/workflows/ci.yml`) bypasses make and runs the uv commands directly — prefer those after the first install.

## Codebase map

Tiny repo (2 top-level dirs). Full table: `.obvious/codebase-map.md`.

| Path | Purpose |
|---|---|
| `hugo_frontmatter_mcp.py` | The entire server — FastMCP app, 15 tools, load/save helpers, `main()` |
| `tests/test_frontmatter_api.py` | 44 pytest tests covering every tool plus error paths |
| `.github/workflows/ci.yml` | lint job (ruff check + format check); test job (pytest on Py 3.10–3.12) |
| `pyproject.toml` / `uv.lock` | metadata, deps, ruff config, lockfile |
| `Makefile`, `Dockerfile`, `smithery.yaml`, `.pre-commit-config.yaml` | build / run / packaging config |

## Local verification

Run after any change; all three must pass (mirrors CI):

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest tests/ -v
```

End-to-end MCP surface check (stdio handshake + tool round-trip): connect with any MCP stdio client, e.g. fastmcp's `Client(StdioTransport("uv", ["run", "hugo_frontmatter_mcp.py"]))`, then `list_tools()` (expect 15) and `call_tool("get_frontmatter", {"file_path": "<absolute path>"})` on a temp `.md` file. **All tool paths must be absolute** — relative paths return an error dict by design.

### Validation Summary (2026-09-06 onboarding run)

- `uv run ruff check .` — pass ("All checks passed!")
- `uv run ruff format --check .` — pass ("3 files already formatted")
- `uv run pytest tests/ -v` — **44/44 passed** in 2.25s
- Live MCP flow over stdio (fastmcp `Client`): initialize handshake OK; 15 tools listed; `get_frontmatter` → `set_title` → `get_field` → `add_tag` → `list_tags_in_directory` all succeeded; the file on disk reflected every write. Exit 0.

## Sandbox snapshot

- Snapshot / template ID: `5tgc4odgqqvi6lg4hrpq:default`
- Built: 2026-09-06T20:22:39.399Z
- Contents: repo at `main` (clean worktree), `.venv` with `.[dev]` deps installed (fastmcp 3.4.5), uv 0.12.10 at `~/.local/bin/uv`

## Notes for agents

- No ports and no long-running process: "dev stack healthy" here means deps installed + lint/format/tests pass + a stdio MCP handshake round-trip works. Do not look for a health endpoint or URL — there is none.
- uv is not preinstalled on a bare sandbox: `curl -LsSf https://astral.sh/uv/install.sh | sh`, then add `~/.local/bin` to PATH.
- `hugo_frontmatter_mcp.py` carries an inline script header (`# /// script`) pinning fastmcp <3.0.0, but `pyproject.toml`/`uv.lock` (what Makefile, CI, and Docker use) pin fastmcp 3.4.5 — the installed version is 3.4.5.
- Pre-commit hooks are configured in `.pre-commit-config.yaml` (ruff v0.9.7 hooks); not part of CI and not run during onboarding.
