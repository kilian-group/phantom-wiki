"""Integration tests for the PhantomWiki MCP server.

Tests the MCP server tools and resources using a temporary dataset directory.
"""

import json
import os
import tempfile

import pytest

from phantom_wiki.mcp_server import (
    _articles,
    _character_names,
    _facts,
    _load_corpus,
    list_all_characters,
    retrieve_article,
    search,
    get_corpus,
)


@pytest.fixture(scope="module", autouse=True)
def setup_corpus(tmp_path_factory):
    """Create a temporary dataset and load it into the MCP server."""
    tmpdir = tmp_path_factory.mktemp("dataset")

    # Create articles.json
    test_data = [
        {
            "title": "Alice Smith",
            "article": "# Alice Smith\n\n## Family\nThe mother of Alice Smith is Jane Smith.\n\n## Attributes\nThe hobby of Alice Smith is reading.",
            "facts": ['mother("Alice Smith", "Jane Smith").', 'hobby("Alice Smith", "reading").'],
        },
        {
            "title": "Bob Jones",
            "article": "# Bob Jones\n\n## Family\nThe father of Bob Jones is Tom Jones.\n\n## Attributes\nThe occupation of Bob Jones is teacher.",
            "facts": ['father("Bob Jones", "Tom Jones").', 'job("Bob Jones", "teacher").'],
        },
        {
            "title": "Jane Smith",
            "article": "# Jane Smith\n\n## Family\nThe daughter of Jane Smith is Alice Smith.\n\n## Attributes\nThe hobby of Jane Smith is gardening.",
            "facts": ['daughter("Jane Smith", "Alice Smith").', 'hobby("Jane Smith", "gardening").'],
        },
    ]

    articles_json = os.path.join(str(tmpdir), "articles.json")
    with open(articles_json, "w") as f:
        json.dump(test_data, f)

    _load_corpus(str(tmpdir))
    yield
    # Clean up global state
    _articles.clear()
    _facts.clear()
    _character_names.clear()


class TestLoadCorpus:
    def test_loads_all_characters(self):
        assert len(_character_names) == 3

    def test_character_names_sorted(self):
        assert _character_names == ["Alice Smith", "Bob Jones", "Jane Smith"]

    def test_articles_loaded(self):
        assert "Alice Smith" in _articles
        assert "# Alice Smith" in _articles["Alice Smith"]

    def test_facts_loaded(self):
        assert "Alice Smith" in _facts
        assert len(_facts["Alice Smith"]) == 2


class TestLoadCorpusFromTxtDir:
    def test_loads_from_articles_dir(self, tmp_path):
        articles_dir = tmp_path / "articles"
        articles_dir.mkdir()
        (articles_dir / "Test Person.txt").write_text("# Test Person\nTest content.")
        (articles_dir / "Test Person_facts.txt").write_text('job("Test Person", "engineer").')

        # Save current state
        old_articles = dict(_articles)
        old_names = list(_character_names)
        old_facts = dict(_facts)

        _articles.clear()
        _facts.clear()
        _character_names.clear()

        _load_corpus(str(tmp_path))
        assert "Test Person" in _articles
        assert len(_character_names) == 1

        # Restore state
        _articles.clear()
        _articles.update(old_articles)
        _facts.clear()
        _facts.update(old_facts)
        _character_names.clear()
        _character_names.extend(old_names)


class TestRetrieveArticle:
    def test_existing_character(self):
        result = retrieve_article("Alice Smith")
        assert "# Alice Smith" in result
        assert "reading" in result

    def test_case_insensitive(self):
        result = retrieve_article("alice smith")
        assert "# Alice Smith" in result

    def test_nonexistent_character(self):
        result = retrieve_article("Nobody")
        assert "No article found" in result


class TestSearch:
    def test_search_by_keyword(self):
        results = search("reading")
        assert "Alice Smith" in results

    def test_search_by_name(self):
        results = search("Bob")
        assert "Bob Jones" in results

    def test_search_case_insensitive(self):
        results = search("TEACHER")
        assert "Bob Jones" in results

    def test_search_no_results(self):
        results = search("xyznonexistent")
        assert len(results) == 0

    def test_search_across_multiple(self):
        results = search("hobby")
        assert "Alice Smith" in results
        assert "Jane Smith" in results


class TestListAllCharacters:
    def test_returns_all(self):
        result = list_all_characters()
        assert len(result) == 3

    def test_sorted(self):
        result = list_all_characters()
        assert result == sorted(result)


class TestGetCorpus:
    def test_returns_valid_json(self):
        result = get_corpus()
        data = json.loads(result)
        assert isinstance(data, list)
        assert len(data) == 3

    def test_corpus_structure(self):
        result = get_corpus()
        data = json.loads(result)
        for entry in data:
            assert "name" in entry
            assert "article" in entry
            assert "facts" in entry
