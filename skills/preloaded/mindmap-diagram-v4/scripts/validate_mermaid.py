"""Validate Mermaid diagram content.

Checks that the input contains a recognized Mermaid diagram type
and optionally validates node count limits.
"""
from __future__ import annotations

import sys
import re

SUPPORTED = ("flowchart", "graph", "mindmap", "sequenceDiagram", "timeline")

# Recommended max node counts by diagram type
NODE_LIMITS = {
    "mindmap": 30,
    "flowchart": 15,
    "graph": 12,
    "sequenceDiagram": 12,
    "timeline": 10,
}


def validate(content: str) -> bool:
    """Check if content contains a supported Mermaid diagram type."""
    return any(item in content for item in SUPPORTED)


def detect_type(content: str) -> str | None:
    """Detect the Mermaid diagram type from content."""
    for dtype in SUPPORTED:
        if dtype in content:
            # 'graph' is a prefix of some false matches, check more carefully
            if dtype == "graph":
                if re.search(r'^graph\s+[TBLR]', content, re.MULTILINE):
                    return dtype
            else:
                return dtype
    return None


def count_nodes(content: str, dtype: str) -> int:
    """Estimate node count from Mermaid content (rough heuristic)."""
    # Count node definitions: [label], {label}, ((label)), (label)
    nodes = set()
    for m in re.finditer(r'[\[\(]\(?([^\]()\)]+)\)?[\]\)]', content):
        label = m.group(1).strip()
        if label:
            nodes.add(label)
    # Also count simple word nodes in mindmap
    if dtype == "mindmap":
        for line in content.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith('mindmap') and not stripped.startswith('root'):
                nodes.add(stripped)
    return len(nodes)


def validate_node_count(content: str) -> tuple[bool, str]:
    """Validate node count against recommended limits.

    Returns (is_ok, message).
    """
    dtype = detect_type(content)
    if dtype is None:
        return True, "Unknown diagram type, skipping node count check."

    limit = NODE_LIMITS.get(dtype, 20)
    count = count_nodes(content, dtype)

    if count <= limit:
        return True, f"Node count {count} is within limit ({limit}) for {dtype}."
    else:
        return False, f"Node count {count} exceeds limit ({limit}) for {dtype}. Consider splitting into multiple diagrams."


if __name__ == "__main__":
    data = sys.stdin.read()
    valid = validate(data)
    print("VALID" if valid else "INVALID")

    if valid:
        ok, msg = validate_node_count(data)
        prefix = "OK" if ok else "WARNING"
        print(f"{prefix}: {msg}")
