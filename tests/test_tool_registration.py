import asyncio

import pytest

import hugo_frontmatter_mcp

EXPECTED_TOOLS = {
    "get_frontmatter",
    "get_field",
    "set_title",
    "set_date",
    "set_publish_date",
    "set_description",
    "set_draft_status",
    "add_tag",
    "remove_tag",
    "add_image",
    "remove_image",
    "list_tags_in_directory",
    "find_posts_by_tag",
    "rename_tag_in_directory",
    "validate_date_formats",
}


def _registered_names():
    tools = asyncio.run(hugo_frontmatter_mcp.mcp_server.list_tools())
    return [tool.name for tool in tools]


def test_registered_tool_set_is_exact():
    names = _registered_names()
    assert len(names) == len(set(names))
    assert set(names) == EXPECTED_TOOLS


@pytest.mark.parametrize("name", sorted(EXPECTED_TOOLS))
def test_registered_name_has_module_level_callable(name):
    assert callable(getattr(hugo_frontmatter_mcp, name, None))


def test_every_registered_name_has_module_level_callable():
    missing = [n for n in _registered_names() if not callable(getattr(hugo_frontmatter_mcp, n, None))]
    assert missing == []
