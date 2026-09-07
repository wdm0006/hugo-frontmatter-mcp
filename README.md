# Hugo Frontmatter MCP

[![smithery badge](https://smithery.ai/badge/@wdm0006/hugo-frontmatter-mcp)](https://smithery.ai/server/@wdm0006/hugo-frontmatter-mcp)

A Model Context Protocol (MCP) server for managing and automating frontmatter operations in [Hugo](https://gohugo.io/) Markdown files. This tool provides a set of programmatic APIs for reading, updating, and validating YAML frontmatter fields, as well as batch operations for tags, images, and date formats across directories.

## Features

- Read and update any frontmatter field in a Hugo Markdown file
- Add/remove tags and images in frontmatter lists
- Set or update title, date, publishDate, description, and draft status
- Batch operations: list all tags, find posts by tag, rename tags, validate date formats
- Designed for automation and integration with other MCP tools

## Install

```bash
# Run directly from GitHub (no install needed)
uvx --from git+https://github.com/wdm0006/hugo-frontmatter-mcp hugo-frontmatter-mcp

# Or install from source
git clone https://github.com/wdm0006/hugo-frontmatter-mcp
cd hugo-frontmatter-mcp
uv sync
uv run hugo_frontmatter_mcp.py
```

### Installing via Smithery

To install hugo-frontmatter-mcp for Claude Desktop automatically via [Smithery](https://smithery.ai/server/@wdm0006/hugo-frontmatter-mcp):

```bash
npx -y @smithery/cli install @wdm0006/hugo-frontmatter-mcp --client claude
```

## MCP Client Configuration

```json
{
  "mcpServers": {
    "hugo-frontmatter": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/wdm0006/hugo-frontmatter-mcp", "hugo-frontmatter-mcp"]
    }
  }
}
```

## API / Tools

The following tools are available:

- `get_frontmatter(file_path)` – Get all frontmatter fields
- `get_field(file_path, field_name)` – Get a specific field
- `set_title(file_path, title)` – Set the title
- `set_date(file_path, date_value)` – Set the date (YYYY-MM-DD)
- `set_publish_date(file_path, publish_date_value)` – Set the publishDate
- `set_description(file_path, description)` – Set the description
- `set_draft_status(file_path, draft_status)` – Set draft status (True/False)
- `add_tag(file_path, tag_to_add)` / `remove_tag(file_path, tag_to_remove)` – Add/remove tags
- `add_image(file_path, image_path_to_add)` / `remove_image(file_path, image_path_to_remove)` – Add/remove images
- `list_tags_in_directory(directory_path_str, recursive=True)` – List all tags in a directory
- `find_posts_by_tag(directory_path_str, tag_to_find, recursive=True)` – Find posts with a specific tag
- `rename_tag_in_directory(directory_path_str, old_tag, new_tag, recursive=True, dry_run=False)` – Rename a tag across posts. With `dry_run=True` the tool reports the files it *would* modify without writing anything
- `validate_date_formats(directory_path_str, field_name="date", expected_format_str="%Y-%m-%d", recursive=True)` – Validate date formats

All file and directory paths must be absolute.

### Tag semantics

A `tags` field can be a YAML list or a bare comma-separated string — both are handled
identically by the batch tools: `tags: "tech, python"` and `tags: [tech, python]` both
count, find, and rename as two tags. Files whose `tags` value is neither a list nor a
string are reported as errors rather than silently skipped.

## Development

```bash
make install          # idempotent: creates .venv only if missing, then syncs dev deps
make lint             # ruff check + format check
make typecheck        # mypy
make test             # pytest with coverage floor (90%) and a 60s per-test timeout
```

Quality gates, all enforced in CI: ruff (via pre-commit), mypy, pytest with a
`--cov-fail-under` coverage floor, and a mutmut 3.7.0 mutation campaign over
`hugo_frontmatter_mcp.py` (`uv run mutmut run`). Surviving mutants are either killed
by a named test or recorded with a classification in
[docs/mutation-waivers.md](docs/mutation-waivers.md).

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
