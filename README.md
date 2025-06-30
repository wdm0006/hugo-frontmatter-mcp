# Hugo Frontmatter MCP

[![smithery badge](https://smithery.ai/badge/@wdm0006/hugo-frontmatter-mcp)](https://smithery.ai/server/@wdm0006/hugo-frontmatter-mcp)

A Model Context Protocol (MCP) server for managing and automating frontmatter operations in [Hugo](https://gohugo.io/) Markdown files. This tool provides a set of programmatic APIs for reading, updating, and validating YAML frontmatter fields, as well as batch operations for tags, images, and date formats across directories.

## Features

- Read and update any frontmatter field in a Hugo Markdown file
- Add/remove tags and images in frontmatter lists
- Set or update title, date, publishDate, description, and draft status
- Batch operations: list all tags, find posts by tag, rename tags, validate date formats
- Designed for automation and integration with other MCP tools

## Installation & Usage

### Installing via Smithery

To install hugo-frontmatter-mcp for Claude Desktop automatically via [Smithery](https://smithery.ai/server/@wdm0006/hugo-frontmatter-mcp):

```bash
npx -y @smithery/cli install @wdm0006/hugo-frontmatter-mcp --client claude
```

### Manual Installation
1. **Clone the repository:**
   ```sh
   git clone https://github.com/wdm0006/hugo-frontmatter-mcp.git
   cd hugo-frontmatter-mcp
   ```
2. **Install [uv](https://github.com/astral-sh/uv) if you don't have it:**
   ```sh
   pip install uv
   ```
3. **Run the MCP server:**
   ```sh
   uv run --with mcp --with python-frontmatter hugo_frontmatter_mcp.py
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
- `rename_tag_in_directory(directory_path_str, old_tag, new_tag, recursive=True)` – Rename a tag across posts
- `validate_date_formats(directory_path_str, field_name="date", expected_format_str="%Y-%m-%d", recursive=True)` – Validate date formats

All file and directory paths must be absolute.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
