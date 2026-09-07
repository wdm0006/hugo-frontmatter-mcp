import os
import pathlib
import re
import tempfile

import frontmatter

import hugo_frontmatter_mcp
from hugo_frontmatter_mcp import (
    add_image,
    add_tag,
    find_posts_by_tag,
    get_field,
    get_frontmatter,
    list_tags_in_directory,
    main,
    remove_image,
    remove_tag,
    rename_tag_in_directory,
    set_date,
    set_description,
    set_draft_status,
    set_publish_date,
    set_title,
    validate_date_formats,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _create_md(fm: dict, content: str = "Sample content.") -> str:
    """Create a temp .md file with the given frontmatter dict. Returns abs path."""
    f = tempfile.NamedTemporaryFile(delete=False, suffix=".md", mode="w")
    post = frontmatter.Post(content, **fm)
    frontmatter.dump(post, f.name)
    f.close()
    return f.name


def _create_md_dir(posts: list[tuple[dict, str]]) -> str:
    """Create a temp directory containing multiple .md files.
    *posts* is a list of (frontmatter_dict, body_text).
    Returns the absolute directory path.
    """
    d = tempfile.mkdtemp()
    for i, (fm, body) in enumerate(posts):
        path = os.path.join(d, f"post{i}.md")
        post = frontmatter.Post(body, **fm)
        frontmatter.dump(post, path)
    return d


# ---------------------------------------------------------------------------
# get_frontmatter / get_field
# ---------------------------------------------------------------------------


class TestGetFrontmatter:
    def test_basic(self):
        p = _create_md({"title": "Hello", "tags": ["a", "b"]})
        try:
            r = get_frontmatter(p)
            assert r["frontmatter"]["title"] == "Hello"
            assert r["frontmatter"]["tags"] == ["a", "b"]
        finally:
            os.unlink(p)

    def test_relative_path_error(self):
        r = get_frontmatter("relative/path.md")
        assert "error" in r

    def test_missing_file_error(self):
        r = get_frontmatter("/tmp/nonexistent_file_abc123.md")
        assert "error" in r


class TestGetField:
    def test_existing_field(self):
        p = _create_md({"title": "T", "draft": True})
        try:
            r = get_field(p, "draft")
            assert r["exists"] is True
            assert r["value"] is True
        finally:
            os.unlink(p)

    def test_missing_field(self):
        p = _create_md({"title": "T"})
        try:
            r = get_field(p, "nonexistent")
            assert r["exists"] is False
            assert r["value"] is None
        finally:
            os.unlink(p)


# ---------------------------------------------------------------------------
# Setters
# ---------------------------------------------------------------------------


class TestSetTitle:
    def test_set_title(self):
        p = _create_md({"title": "Old"})
        try:
            r = set_title(p, "New")
            assert r["new_value"] == "New"
            assert get_frontmatter(p)["frontmatter"]["title"] == "New"
        finally:
            os.unlink(p)

    def test_preserves_frontmatter_key_order(self, tmp_path: pathlib.Path):
        post_path = tmp_path / "post.md"
        post_path.write_text(
            """---
title: My Post
date: '2024-01-15'
draft: false
tags: [python, hugo]
description: Hello
---
Sample content.
"""
        )

        set_title(str(post_path), "My New Post")

        raw_post = post_path.read_text()
        assert "title: My New Post" in raw_post
        frontmatter_lines = raw_post.split("---", 2)[1].strip().splitlines()
        top_level_keys = [line.split(":", 1)[0] for line in frontmatter_lines if ":" in line and not line[0].isspace()]
        assert top_level_keys == [
            "title",
            "date",
            "draft",
            "tags",
            "description",
        ]

    def test_wrong_type(self):
        p = _create_md({"title": "Old"})
        try:
            r = set_title(p, 123)  # type: ignore[arg-type]
            assert "error" in r
        finally:
            os.unlink(p)


class TestSetDate:
    def test_set_date(self):
        p = _create_md({"date": "2024-01-01"})
        try:
            r = set_date(p, "2025-06-15")
            assert r["new_value"] == "2025-06-15"
            assert "warning" not in r
        finally:
            os.unlink(p)

    def test_warns_for_invalid_format_after_writing(self):
        p = _create_md({"date": "2024-01-01"})
        try:
            r = set_date(p, "Jan 5 2024")
            assert r["warning"] == "Value 'Jan 5 2024' does not match the expected date format %Y-%m-%d."
            assert get_frontmatter(p)["frontmatter"]["date"] == "Jan 5 2024"
        finally:
            os.unlink(p)

    def test_wrong_type_is_rejected_without_a_warning(self):
        p = _create_md({"date": "2024-01-01"})
        try:
            r = set_date(p, 20240101)  # type: ignore[arg-type]
            assert "error" in r
            assert "warning" not in r
            assert get_frontmatter(p)["frontmatter"]["date"] == "2024-01-01"
        finally:
            os.unlink(p)

    def test_other_setters_never_warn(self):
        p = _create_md({})
        try:
            assert "warning" not in set_title(p, "Jan 5 2024")
            assert "warning" not in set_description(p, "not a date")
        finally:
            os.unlink(p)


class TestSetPublishDate:
    def test_set_publish_date(self):
        p = _create_md({})
        try:
            r = set_publish_date(p, "2025-07-01")
            assert r["new_value"] == "2025-07-01"
            assert "warning" not in r
            assert get_frontmatter(p)["frontmatter"]["publishDate"] == "2025-07-01"
        finally:
            os.unlink(p)

    def test_warns_for_invalid_format_after_writing(self):
        p = _create_md({})
        try:
            r = set_publish_date(p, "20204-01-01")
            assert r["warning"] == "Value '20204-01-01' does not match the expected date format %Y-%m-%d."
            assert get_frontmatter(p)["frontmatter"]["publishDate"] == "20204-01-01"
        finally:
            os.unlink(p)


class TestSetDescription:
    def test_set_description(self):
        p = _create_md({})
        try:
            r = set_description(p, "A short description")
            assert r["new_value"] == "A short description"
        finally:
            os.unlink(p)


class TestSetDraftStatus:
    def test_set_draft_true(self):
        p = _create_md({"draft": False})
        try:
            r = set_draft_status(p, True)
            assert r["new_value"] is True
        finally:
            os.unlink(p)

    def test_wrong_type(self):
        p = _create_md({})
        try:
            r = set_draft_status(p, "yes")  # type: ignore[arg-type]
            assert "error" in r
        finally:
            os.unlink(p)


# ---------------------------------------------------------------------------
# Tags
# ---------------------------------------------------------------------------


class TestAddTag:
    def test_add_new_tag(self):
        p = _create_md({"tags": ["python"]})
        try:
            r = add_tag(p, "mcp")
            assert "added" in r.get("message", "").lower() or "mcp" in r.get("message", "")
            fm = get_frontmatter(p)["frontmatter"]
            assert "mcp" in fm["tags"]
        finally:
            os.unlink(p)

    def test_add_duplicate_tag(self):
        p = _create_md({"tags": ["python"]})
        try:
            r = add_tag(p, "python")
            assert "already exists" in r.get("message", "").lower()
        finally:
            os.unlink(p)

    def test_add_tag_creates_list(self):
        p = _create_md({})
        try:
            add_tag(p, "new")
            fm = get_frontmatter(p)["frontmatter"]
            assert "new" in fm["tags"]
        finally:
            os.unlink(p)

    def test_empty_tag_error(self):
        p = _create_md({"tags": []})
        try:
            r = add_tag(p, "")
            assert "error" in r
        finally:
            os.unlink(p)


class TestRemoveTag:
    def test_remove_existing(self):
        p = _create_md({"tags": ["a", "b", "c"]})
        try:
            remove_tag(p, "b")
            fm = get_frontmatter(p)["frontmatter"]
            assert "b" not in fm["tags"]
            assert len(fm["tags"]) == 2
        finally:
            os.unlink(p)

    def test_remove_nonexistent(self):
        p = _create_md({"tags": ["a"]})
        try:
            r = remove_tag(p, "z")
            assert "not found" in r.get("message", "").lower()
        finally:
            os.unlink(p)


# ---------------------------------------------------------------------------
# Images
# ---------------------------------------------------------------------------


class TestAddImage:
    def test_add_image(self):
        p = _create_md({"images": ["/img/a.png"]})
        try:
            add_image(p, "/img/b.png")
            fm = get_frontmatter(p)["frontmatter"]
            assert "/img/b.png" in fm["images"]
        finally:
            os.unlink(p)

    def test_empty_image_error(self):
        p = _create_md({})
        try:
            r = add_image(p, "")
            assert "error" in r
        finally:
            os.unlink(p)


class TestRemoveImage:
    def test_remove_image(self):
        p = _create_md({"images": ["/img/a.png", "/img/b.png"]})
        try:
            remove_image(p, "/img/a.png")
            fm = get_frontmatter(p)["frontmatter"]
            assert "/img/a.png" not in fm["images"]
        finally:
            os.unlink(p)


# ---------------------------------------------------------------------------
# Batch / directory operations
# ---------------------------------------------------------------------------


class TestListTagsInDirectory:
    def test_counts_tags(self):
        d = _create_md_dir(
            [
                ({"tags": ["python", "mcp"]}, "post 1"),
                ({"tags": ["python", "ai"]}, "post 2"),
                ({"tags": ["mcp"]}, "post 3"),
                ({"tags": []}, "post 4"),
            ]
        )
        try:
            r = list_tags_in_directory(d)
            assert r["files_processed"] == 4
            assert r["files_with_tags"] == 4
            assert r["tag_counts"]["python"] == 2
            assert r["tag_counts"]["mcp"] == 2
            assert r["tag_counts"]["ai"] == 1
        finally:
            for f in pathlib.Path(d).glob("*.md"):
                f.unlink()
            os.rmdir(d)

    def test_relative_path_error(self):
        r = list_tags_in_directory("relative/dir")
        assert "error" in r

    def test_counts_bare_string_tag(self):
        d = _create_md_dir([({"tags": "python"}, "post")])
        try:
            r = list_tags_in_directory(d)
            assert r["files_with_tags"] == 1
            assert r["tag_counts"] == {"python": 1}
        finally:
            for f in pathlib.Path(d).glob("*.md"):
                f.unlink()
            os.rmdir(d)

    def test_counts_comma_separated_bare_string_tags(self):
        d = _create_md_dir([({"tags": "tech, python"}, "post")])
        try:
            r = list_tags_in_directory(d)
            assert r["files_with_tags"] == 1
            assert r["tag_counts"] == {"tech": 1, "python": 1}
        finally:
            for f in pathlib.Path(d).glob("*.md"):
                f.unlink()
            os.rmdir(d)

    def test_reports_non_string_tags_in_list(self):
        d = _create_md_dir([({"tags": [123, "python"]}, "post")])
        try:
            r = list_tags_in_directory(d)
            # String tags still count...
            assert r["tag_counts"] == {"python": 1}
            # ...and the non-string tag is reported instead of silently skipped.
            assert len(r["errors"]) == 1
            assert "non-string" in r["errors"][0]["error"]
            assert r["errors"][0]["file_path"] == os.path.join(d, "post0.md")
        finally:
            for f in pathlib.Path(d).glob("*.md"):
                f.unlink()
            os.rmdir(d)

    def test_missing_dir_error(self):
        r = list_tags_in_directory("/tmp/nonexistent_dir_abc123")
        assert "error" in r

    def test_reports_malformed_files(self):
        d = _create_md_dir(
            [
                ({"tags": ["python"]}, "valid post"),
            ]
        )
        bad = os.path.join(d, "broken.md")
        with open(bad, "w") as handle:
            handle.write("---\ntags: [unclosed\ntitle: broken\n---\nbody\n")
        try:
            r = list_tags_in_directory(d)
            # Valid file is still counted correctly.
            assert r["tag_counts"]["python"] == 1
            # The malformed file is reported rather than silently skipped.
            assert len(r["errors"]) == 1
            assert r["errors"][0]["file_path"] == bad
        finally:
            for f in pathlib.Path(d).glob("*.md"):
                f.unlink()
            os.rmdir(d)


class TestFindPostsByTag:
    def test_finds_matching_posts(self):
        d = _create_md_dir(
            [
                ({"tags": ["python"]}, "p1"),
                ({"tags": ["rust"]}, "p2"),
                ({"tags": ["python", "rust"]}, "p3"),
            ]
        )
        try:
            r = find_posts_by_tag(d, "python")
            assert len(r["matching_files"]) == 2
        finally:
            for f in pathlib.Path(d).glob("*.md"):
                f.unlink()
            os.rmdir(d)

    def test_no_matches(self):
        d = _create_md_dir(
            [
                ({"tags": ["a"]}, "p"),
            ]
        )
        try:
            r = find_posts_by_tag(d, "nonexistent")
            assert len(r["matching_files"]) == 0
        finally:
            for f in pathlib.Path(d).glob("*.md"):
                f.unlink()
            os.rmdir(d)

    def test_finds_post_with_bare_string_tag(self):
        d = _create_md_dir([({"tags": "python"}, "post")])
        try:
            r = find_posts_by_tag(d, "python")
            assert r["matching_files"] == [os.path.join(d, "post0.md")]
        finally:
            for f in pathlib.Path(d).glob("*.md"):
                f.unlink()
            os.rmdir(d)

    def test_finds_tag_within_comma_separated_bare_string(self):
        d = _create_md_dir([({"tags": "tech, python"}, "post")])
        try:
            r = find_posts_by_tag(d, "python")
            assert r["matching_files"] == [os.path.join(d, "post0.md")]
        finally:
            for f in pathlib.Path(d).glob("*.md"):
                f.unlink()
            os.rmdir(d)

    def test_reports_malformed_files(self):
        d = _create_md_dir(
            [
                ({"tags": ["python"]}, "valid post"),
            ]
        )
        bad = os.path.join(d, "broken.md")
        with open(bad, "w") as handle:
            handle.write("---\ntags: [unclosed\ntitle: broken\n---\nbody\n")
        try:
            r = find_posts_by_tag(d, "python")
            # Valid matching file is still found.
            assert len(r["matching_files"]) == 1
            # The malformed file is reported rather than silently skipped.
            assert len(r["errors"]) == 1
            assert r["errors"][0]["file_path"] == bad
        finally:
            for f in pathlib.Path(d).glob("*.md"):
                f.unlink()
            os.rmdir(d)


class TestRenameTagInDirectory:
    def test_renames_tag(self):
        d = _create_md_dir(
            [
                ({"tags": ["old", "keep"]}, "p1"),
                ({"tags": ["old"]}, "p2"),
                ({"tags": ["other"]}, "p3"),
            ]
        )
        try:
            r = rename_tag_in_directory(d, "old", "new")
            assert len(r["modified_files"]) == 2

            # Verify the files were actually modified
            for md in pathlib.Path(d).glob("*.md"):
                post = frontmatter.load(str(md))
                tags = post.metadata.get("tags", [])
                assert "old" not in tags
        finally:
            for f in pathlib.Path(d).glob("*.md"):
                f.unlink()
            os.rmdir(d)

    def test_skips_symlinks(self, tmp_path):
        content_dir = tmp_path / "content"
        content_dir.mkdir()
        outside = tmp_path / "outside.md"
        frontmatter.dump(frontmatter.Post("outside", tags=["old"]), str(outside))
        outside_bytes = outside.read_bytes()

        frontmatter.dump(frontmatter.Post("inside", tags=["old"]), str(content_dir / "post.md"))
        (content_dir / "linked.md").symlink_to(outside)

        result = rename_tag_in_directory(str(content_dir), "old", "new")

        assert result["modified_files"] == [str(content_dir / "post.md")]
        assert outside.read_bytes() == outside_bytes
        symlink_errors = [e for e in result["errors"] if e["file_path"] == str(content_dir / "linked.md")]
        assert len(symlink_errors) == 1
        assert "symlink" in symlink_errors[0]["error"].lower()
        assert frontmatter.load(str(content_dir / "post.md")).metadata["tags"] == ["new"]

    def test_same_tag_noop(self):
        d = _create_md_dir([({"tags": ["a"]}, "p")])
        try:
            r = rename_tag_in_directory(d, "a", "a")
            assert "same" in r.get("message", "").lower()
        finally:
            for f in pathlib.Path(d).glob("*.md"):
                f.unlink()
            os.rmdir(d)

    def test_renames_simple_bare_string_tag(self):
        d = _create_md_dir([({"tags": "old"}, "p1")])
        try:
            r = rename_tag_in_directory(d, "old", "new")
            assert r["modified_files"] == [os.path.join(d, "post0.md")]
            post = frontmatter.load(os.path.join(d, "post0.md"))
            assert post.metadata["tags"] == ["new"]
        finally:
            for f in pathlib.Path(d).glob("*.md"):
                f.unlink()
            os.rmdir(d)

    def test_renames_comma_separated_bare_string_tags(self):
        # Previously silent: the fuzzy prefilter matched but the exact-equality
        # rename never fired, so "tech, python" was never touched.
        d = _create_md_dir([({"tags": "tech, python"}, "p1")])
        try:
            r = rename_tag_in_directory(d, "tech", "development")
            assert r["modified_files"] == [os.path.join(d, "post0.md")]
            post = frontmatter.load(os.path.join(d, "post0.md"))
            # New tag is appended after the remaining tags, matching the
            # list-valued rename behavior.
            assert post.metadata["tags"] == ["python", "development"]
        finally:
            for f in pathlib.Path(d).glob("*.md"):
                f.unlink()
            os.rmdir(d)

    def test_comma_separated_rename_targets_only_requested_tag(self):
        d = _create_md_dir([({"tags": "tech, python"}, "p1")])
        try:
            r = rename_tag_in_directory(d, "python", "code")
            assert r["modified_files"] == [os.path.join(d, "post0.md")]
            post = frontmatter.load(os.path.join(d, "post0.md"))
            assert post.metadata["tags"] == ["tech", "code"]
        finally:
            for f in pathlib.Path(d).glob("*.md"):
                f.unlink()
            os.rmdir(d)

    def test_dry_run_reports_without_writing(self):
        d = _create_md_dir([({"tags": ["old"]}, "p1"), ({"tags": ["keep"]}, "p2")])
        try:
            before = {f.name: f.read_bytes() for f in pathlib.Path(d).glob("*.md")}

            r = rename_tag_in_directory(d, "old", "new", dry_run=True)

            assert r["dry_run"] is True
            assert r["modified_files"] == [os.path.join(d, "post0.md")]
            after = {f.name: f.read_bytes() for f in pathlib.Path(d).glob("*.md")}
            assert after == before

            # The real rename still applies afterwards.
            r2 = rename_tag_in_directory(d, "old", "new")
            assert r2["dry_run"] is False
            assert r2["modified_files"] == [os.path.join(d, "post0.md")]
            post = frontmatter.load(os.path.join(d, "post0.md"))
            assert post.metadata["tags"] == ["new"]
        finally:
            for f in pathlib.Path(d).glob("*.md"):
                f.unlink()
            os.rmdir(d)

    def test_reports_malformed_tags_type_instead_of_silent_skip(self):
        d = _create_md_dir([({"tags": 42}, "p1")])
        try:
            r = rename_tag_in_directory(d, "old", "new")
            assert r["modified_files"] == []
            assert len(r["errors"]) == 1
            assert "not a list or string" in r["errors"][0]["error"]
            assert r["errors"][0]["file_path"] == os.path.join(d, "post0.md")
            # The file is untouched.
            post = frontmatter.load(os.path.join(d, "post0.md"))
            assert post.metadata["tags"] == 42
        finally:
            for f in pathlib.Path(d).glob("*.md"):
                f.unlink()
            os.rmdir(d)

    def test_files_without_tags_are_not_errors(self):
        d = _create_md_dir([({"title": "no tags"}, "p1"), ({"tags": ["old"]}, "p2")])
        try:
            r = rename_tag_in_directory(d, "old", "new")
            assert r["modified_files"] == [os.path.join(d, "post1.md")]
            assert r["errors"] == []
        finally:
            for f in pathlib.Path(d).glob("*.md"):
                f.unlink()
            os.rmdir(d)


class TestValidateDateFormats:
    def test_native_yaml_date(self, tmp_path):
        (tmp_path / "post.md").write_text("---\ndate: 2025-06-15\n---\n")

        result = validate_date_formats(str(tmp_path))

        assert result["files_with_field"] == 1
        assert result["invalid_date_entries"] == []

    def test_valid_dates(self):
        d = _create_md_dir(
            [
                ({"date": "2025-01-15"}, "p1"),
                ({"date": "2024-12-31"}, "p2"),
            ]
        )
        try:
            r = validate_date_formats(d)
            assert r["files_with_field"] == 2
            assert len(r["invalid_date_entries"]) == 0
        finally:
            for f in pathlib.Path(d).glob("*.md"):
                f.unlink()
            os.rmdir(d)

    def test_invalid_date_format(self):
        d = _create_md_dir(
            [
                ({"date": "Jan 15, 2025"}, "p1"),
                ({"date": "2025-01-15"}, "p2"),
            ]
        )
        try:
            r = validate_date_formats(d)
            assert len(r["invalid_date_entries"]) == 1
        finally:
            for f in pathlib.Path(d).glob("*.md"):
                f.unlink()
            os.rmdir(d)

    def test_missing_date_field(self):
        d = _create_md_dir(
            [
                ({"title": "no date here"}, "p1"),
            ]
        )
        try:
            r = validate_date_formats(d)
            assert r["files_with_field"] == 0
            assert len(r["invalid_date_entries"]) == 0
        finally:
            for f in pathlib.Path(d).glob("*.md"):
                f.unlink()
            os.rmdir(d)

    def test_relative_path_error(self):
        r = validate_date_formats("relative/dir")
        assert "error" in r


# ---------------------------------------------------------------------------
# Entry point (stdio transport keeps stdout reserved for JSON-RPC)
# ---------------------------------------------------------------------------


class TestScriptHeaderParity:
    """The PEP 723 header and pyproject must pin fastmcp identically.

    `uv run hugo_frontmatter_mcp.py` resolves dependencies from the inline
    header, while pip/uvx installs resolve from pyproject — a drift between
    them means the two entry points run different fastmcp majors.
    """

    def test_pep723_fastmcp_pin_matches_pyproject(self):
        module_path = pathlib.Path(hugo_frontmatter_mcp.__file__).resolve()
        script = module_path.read_text()

        header = re.search(r"# /// script\n(.*?)# ///", script, re.DOTALL)
        assert header, "PEP 723 script header missing"

        header_reqs = re.findall(r'"(fastmcp[^"]*)"', header.group(1))
        pyproject_text = (module_path.parent / "pyproject.toml").read_text()
        pyproject_reqs = re.findall(r'"(fastmcp[^"]*)"', pyproject_text)

        assert header_reqs, "no fastmcp requirement in PEP 723 header"
        assert pyproject_reqs, "no fastmcp requirement in pyproject"
        assert header_reqs == pyproject_reqs


class TestMain:
    def test_startup_message_goes_to_stderr(self, monkeypatch, capsys):
        monkeypatch.setattr(hugo_frontmatter_mcp.mcp_server, "run", lambda: None)
        main()
        captured = capsys.readouterr()
        assert captured.out == ""
        assert "Starting Hugo Frontmatter MCP server" in captured.err
