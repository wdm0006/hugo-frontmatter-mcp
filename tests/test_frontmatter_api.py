import os
import tempfile
import frontmatter
import pytest
from hugo_frontmatter_mcp import get_frontmatter, set_title

def create_temp_md_with_frontmatter(frontmatter_dict, content="Sample content."):
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".md")
    post = frontmatter.Post(content, **frontmatter_dict)
    frontmatter.dump(post, temp.name)
    return temp.name

def test_get_and_set_frontmatter():
    # Create a temp markdown file with some frontmatter
    initial_title = "Initial Title"
    file_path = create_temp_md_with_frontmatter({"title": initial_title, "tags": ["test"]})
    try:
        # Test get_frontmatter
        result = get_frontmatter(file_path)
        assert result["frontmatter"]["title"] == initial_title
        assert "tags" in result["frontmatter"]

        # Test set_title
        new_title = "Updated Title"
        set_result = set_title(file_path, new_title)
        assert set_result["new_value"] == new_title
        # Confirm the file was updated
        result2 = get_frontmatter(file_path)
        assert result2["frontmatter"]["title"] == new_title
    finally:
        os.remove(file_path) 