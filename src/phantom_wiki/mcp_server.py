"""MCP (Model Context Protocol) server for PhantomWiki.

Exposes the PhantomWiki corpus as MCP tools for agentic evaluation.
Any MCP-compatible agent can connect to this server to query the corpus.

Tools:
    - retrieve_article(name) -> article text
    - search(query) -> list of matching article titles
    - list_all_characters() -> list of all character names

Resource:
    - phantom-wiki://corpus -> full corpus as JSON

Usage:
    phantom-wiki-mcp-server --dataset-dir <path>
"""

import json
import logging
import os
import sys
from argparse import ArgumentParser

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

# Global state set during server initialization
_articles: dict[str, str] = {}
_facts: dict[str, list[str]] = {}
_character_names: list[str] = []

mcp = FastMCP("phantom-wiki")


def _load_corpus(dataset_dir: str) -> None:
    """Load the PhantomWiki corpus from a dataset directory.

    Supports two formats:
    - articles/ directory with .txt files
    - articles.json file
    """
    global _articles, _facts, _character_names

    articles_json = os.path.join(dataset_dir, "articles.json")
    articles_dir = os.path.join(dataset_dir, "articles")

    if os.path.exists(articles_json):
        with open(articles_json) as f:
            data = json.load(f)
        for entry in data:
            name = entry["title"]
            _articles[name] = entry["article"]
            _facts[name] = entry.get("facts", [])
    elif os.path.isdir(articles_dir):
        for filename in sorted(os.listdir(articles_dir)):
            if filename.endswith(".txt") and not filename.endswith("_facts.txt"):
                name = filename[:-4]  # Remove .txt
                with open(os.path.join(articles_dir, filename)) as f:
                    _articles[name] = f.read()
                facts_file = os.path.join(articles_dir, f"{name}_facts.txt")
                if os.path.exists(facts_file):
                    with open(facts_file) as f:
                        _facts[name] = f.read().strip().split("\n")
    else:
        raise FileNotFoundError(
            f"No articles found in {dataset_dir}. "
            "Expected either articles.json or articles/ directory."
        )

    _character_names.clear()
    _character_names.extend(sorted(_articles.keys()))
    logger.info(f"Loaded {len(_character_names)} character articles from {dataset_dir}")


@mcp.tool()
def retrieve_article(name: str) -> str:
    """Retrieve the article for a character by name.

    Args:
        name: The full name of the character (e.g., "Alice Smith").

    Returns:
        The article text, or an error message if not found.
    """
    if name in _articles:
        return _articles[name]

    # Try case-insensitive match
    name_lower = name.lower()
    for char_name in _character_names:
        if char_name.lower() == name_lower:
            return _articles[char_name]

    return f"No article found for '{name}'. Use list_all_characters() to see available names."


@mcp.tool()
def search(query: str) -> list[str]:
    """Search for characters whose articles contain the query string.

    Performs case-insensitive keyword search across all articles.

    Args:
        query: The search query string.

    Returns:
        List of character names whose articles match the query.
    """
    query_lower = query.lower()
    matches = []
    for name, article in _articles.items():
        if query_lower in article.lower() or query_lower in name.lower():
            matches.append(name)
    return sorted(matches)


@mcp.tool()
def list_all_characters() -> list[str]:
    """List all character names in the corpus.

    Returns:
        Sorted list of all character names.
    """
    return _character_names


@mcp.resource("phantom-wiki://corpus")
def get_corpus() -> str:
    """Get the full PhantomWiki corpus as JSON.

    Returns:
        JSON string with all articles and their facts.
    """
    corpus = [
        {"name": name, "article": _articles[name], "facts": _facts.get(name, [])}
        for name in _character_names
    ]
    return json.dumps(corpus, indent=2)


def main():
    """CLI entrypoint for the PhantomWiki MCP server."""
    parser = ArgumentParser(description="PhantomWiki MCP Server")
    parser.add_argument(
        "--dataset-dir",
        type=str,
        required=True,
        help="Path to the PhantomWiki dataset directory (containing articles/ or articles.json)",
    )
    parser.add_argument(
        "--transport",
        type=str,
        default="stdio",
        choices=["stdio", "sse"],
        help="MCP transport protocol (default: stdio)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for SSE transport (default: 8000)",
    )

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    _load_corpus(args.dataset_dir)

    if args.transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="sse")


if __name__ == "__main__":
    main()
