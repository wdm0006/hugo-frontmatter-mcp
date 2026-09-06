---
name: local-dev
description: Stand up and verify a local dev environment for wdm0006/hugo-frontmatter-mcp — a Python stdio MCP server managed with uv, verified with ruff, pytest, and a live MCP client round-trip.
---

# local-dev — hugo-frontmatter-mcp

Durable record of the 2026-09-06 onboarding run that produced sandbox snapshot `5tgc4odgqqvi6lg4hrpq:default`.

## What this stack is

A single-module MCP server (`hugo_frontmatter_mcp.py`) that runs over **stdio**. There is no HTTP port, no daemon, no database, and no required env vars. "Dev stack healthy" = deps installed + lint/format/tests pass + an MCP stdio handshake round-trip works.

## Setup from a bare sandbox

```bash
# 1. uv is not preinstalled
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

# 2. Install deps (fresh checkout; Makefile path)
make install                      # uv venv .venv --seed && uv pip install -e ".[dev]"
# If .venv already exists:
UV_VENV_CLEAR=1 make install
```

CI equivalent (no make): `uv venv .venv && uv pip install -e ".[dev]"`.

## Verify (must all pass)

```bash
uv run ruff check .               # expect: All checks passed!
uv run ruff format --check .      # expect: N files already formatted
uv run pytest tests/ -v           # expect: 44 passed
```

## Run the app

```bash
uv run hugo_frontmatter_mcp.py    # or: uv run hugo-frontmatter-mcp
```

Stdio server; startup line `Starting Hugo Frontmatter MCP server. Expects absolute paths.` goes to stderr. It exits when the client disconnects — run it under an MCP client, not bare, for meaningful verification.

## End-to-end MCP round-trip (primary flow)

```python
import asyncio
from fastmcp import Client
from fastmcp.client.transports import StdioTransport


async def main():
    transport = StdioTransport("uv", ["run", "hugo_frontmatter_mcp.py"], cwd="/home/user/work/hugo-frontmatter-mcp")
    async with Client(transport) as client:
        tools = await client.list_tools()  # expect 15 tools
        r = await client.call_tool("get_frontmatter", {"file_path": "/abs/path/post.md"})
        print(r.data)


asyncio.run(main())
```

Verified flow on 2026-09-06: initialize OK → 15 tools listed → `get_frontmatter` read → `set_title` wrote → `get_field` confirmed new title → `add_tag` appended → `list_tags_in_directory` batch op → file on disk reflected every write. Exit 0.

## Quirks

- **Makefile venv quirk:** `install` is a prerequisite of `lint`/`lint-check`/`format`/`format-check`/`test` and unconditionally runs `uv venv .venv --seed`, which fails when `.venv` exists. Either `UV_VENV_CLEAR=1 make <target>` (recreates the venv every time) or run the direct `uv run ...` commands — CI does the latter.
- **Absolute paths only:** every tool rejects relative paths with an error dict; directory tools require absolute directory paths.
- **Version pins differ:** the inline script header in `hugo_frontmatter_mcp.py` says fastmcp <3.0.0, but `pyproject.toml`/`uv.lock` pin 3.4.5 — 3.4.5 is what Makefile/CI/Docker install.
- **No leftover locks:** check for an existing `.venv` before `make install` (this is the only "lock" that matters here).

## Evidence captured (2026-09-06 run)

- ruff check: pass — `All checks passed!`
- ruff format --check: pass — `3 files already formatted`
- pytest: `44 passed in 2.25s` (also `44 passed in 2.29s` via `UV_VENV_CLEAR=1 make test`)
- MCP stdio client transcript: handshake OK, 15 tools, read/write/batch round-trip, on-disk file updated, exit 0

## Snapshot

- Template ID: `5tgc4odgqqvi6lg4hrpq:default` (built 2026-09-06T20:22:39.399Z)
- Restores: repo at `main`, `.venv` with `.[dev]` deps (fastmcp 3.4.5), uv 0.12.10 at `~/.local/bin/uv`
