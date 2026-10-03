import threading
import time
from concurrent.futures import ThreadPoolExecutor

import frontmatter
import pytest

import hugo_frontmatter_mcp as api


@pytest.fixture
def slow_load(monkeypatch):
    original_load = api._load_post

    def load(file_path):
        result = original_load(file_path)
        time.sleep(0.01)
        return result

    monkeypatch.setattr(api, "_load_post", load)


def _run_concurrently(calls):
    barrier = threading.Barrier(len(calls))

    def run(call):
        barrier.wait(timeout=10)
        return call()

    with ThreadPoolExecutor(max_workers=len(calls)) as pool:
        results = list(pool.map(run, calls))
    for result in results:
        assert "error" not in result
        assert not result.get("errors")


@pytest.mark.parametrize("trial", range(5))
def test_parallel_add_tags(tmp_path, slow_load, trial):
    post_path = tmp_path / f"post-{trial}.md"
    frontmatter.dump(frontmatter.Post("Body", tags=["base"]), str(post_path))
    tags = [f"tag-{i}" for i in range(12)]
    _run_concurrently([lambda tag=tag: api.add_tag(str(post_path), tag) for tag in tags])
    post = frontmatter.load(str(post_path))
    assert set(post.metadata["tags"]) == {"base", *tags}
    assert post.content == "Body"


@pytest.mark.parametrize("trial", range(5))
def test_parallel_scalar_updates(tmp_path, slow_load, trial):
    post_path = tmp_path / f"post-{trial}.md"
    frontmatter.dump(frontmatter.Post("Body", tags=["base"]), str(post_path))
    _run_concurrently(
        [
            lambda: api.set_title(str(post_path), "New title"),
            lambda: api.set_description(str(post_path), "New description"),
        ]
    )
    post = frontmatter.load(str(post_path))
    assert post.metadata["title"] == "New title"
    assert post.metadata["description"] == "New description"
    assert post.metadata["tags"] == ["base"]


def test_parallel_rename_and_setter(tmp_path, slow_load):
    post_path = tmp_path / "post.md"
    frontmatter.dump(frontmatter.Post("Body", tags=["old"]), str(post_path))
    _run_concurrently(
        [
            lambda: api.rename_tag_in_directory(str(tmp_path), "old", "new"),
            lambda: api.set_title(str(post_path), "New title"),
        ]
    )
    post = frontmatter.load(str(post_path))
    assert post.metadata["tags"] == ["new"]
    assert post.metadata["title"] == "New title"


def test_file_lock_resolves_aliases_and_concurrent_first_touches(tmp_path):
    post_path = tmp_path / "post.md"
    post_path.touch()
    alias = tmp_path / "alias.md"
    alias.symlink_to(post_path)
    barrier = threading.Barrier(12)

    def get_lock(i):
        barrier.wait(timeout=10)
        return api._file_lock(str(alias if i % 2 else post_path))

    with ThreadPoolExecutor(max_workers=12) as pool:
        locks = list(pool.map(get_lock, range(12)))
    assert all(lock is locks[0] for lock in locks)
    assert api._file_lock(str(tmp_path / "other.md")) is not locks[0]
