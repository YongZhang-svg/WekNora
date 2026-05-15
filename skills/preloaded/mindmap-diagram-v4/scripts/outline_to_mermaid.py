"""Convert a markdown outline into Mermaid mindmap.

Supports:
- Headings written with #, ##, ###, ####
- List items written with - or * and indentation
- Mixed heading + list outlines

Output is a Mermaid mindmap with proper indentation.
"""
from __future__ import annotations

import sys
import re
from dataclasses import dataclass


@dataclass
class Node:
    level: int
    title: str


def parse_outline(text: str) -> list[Node]:
    """Parse markdown outline into a list of (level, title) nodes.

    Supports both heading syntax (# ## ###) and list syntax (- / * with indent).
    """
    nodes: list[Node] = []
    for line in text.splitlines():
        line = line.rstrip()
        stripped = line.lstrip()

        if not stripped:
            continue

        # Heading syntax: # Title
        if stripped.startswith('#'):
            n_hashes = len(stripped) - len(stripped.lstrip('#'))
            title = stripped[n_hashes:].strip()
            if title:
                nodes.append(Node(level=n_hashes, title=title))
            continue

        # List syntax: - Item or * Item
        list_match = re.match(r'^(\s*)[-*]\s+(.+)$', line)
        if list_match:
            indent = len(list_match.group(1))
            title = list_match.group(2).strip()
            # Convert indent to level: every 2 spaces = 1 level, minimum level 2
            level = 2 + indent // 2
            if title:
                nodes.append(Node(level=level, title=title))
            continue

    return nodes


def to_mermaid(nodes: list[Node]) -> str:
    """Convert parsed nodes to Mermaid mindmap syntax.

    Properly handles indentation based on relative depth.
    """
    if not nodes:
        return "mindmap\n  root((Topic))"

    root = nodes[0].title
    out = ["mindmap", f"  root(({root}))"]

    # Normalize levels: make root level 1, everything else relative
    min_level = min(n.level for n in nodes[1:]) if len(nodes) > 1 else 2

    for node in nodes[1:]:
        # Calculate relative depth (1-indexed from root)
        relative_depth = max(1, node.level - min_level + 1)
        indent = "  " * (relative_depth + 1)  # +1 for root offset
        out.append(f"{indent}{node.title}")

    return "\n".join(out)


if __name__ == "__main__":
    text = sys.stdin.read()
    nodes = parse_outline(text)
    print(to_mermaid(nodes))
