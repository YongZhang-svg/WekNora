"""Split overly large outlines into multiple chunks for easier diagramming.

Supports both heading-based and line-count-based splitting.
Heading-based splitting keeps sections intact when possible.
"""
from __future__ import annotations

import sys
import re

MAX_LINES = 25  # fallback: max lines per chunk


def split_by_headings(text_lines: list[str]) -> list[list[str]]:
    """Split by top-level headings (##), keeping each section intact.

    If a single section exceeds MAX_LINES, fall back to line-count splitting
    for that section only.
    """
    chunks: list[list[str]] = []
    current: list[str] = []
    current_heading = ""

    for line in text_lines:
        # Detect top-level heading (## exactly, not ###)
        if re.match(r'^##\s+', line) and not re.match(r'^###\s+', line):
            if current:
                chunks.append(current)
            current_heading = line.strip()
            current = [line]
        else:
            current.append(line)

        # Fallback: if current chunk is too large, split it
        if len(current) >= MAX_LINES * 2:
            chunks.append(current[:MAX_LINES])
            current = current[MAX_LINES:]

    if current:
        chunks.append(current)

    return chunks


def split_by_line_count(text_lines: list[str]) -> list[list[str]]:
    """Simple line-count based splitting (original logic)."""
    chunks: list[list[str]] = []
    current: list[str] = []

    for line in text_lines:
        if line.strip():
            current.append(line)
        if len(current) >= MAX_LINES:
            chunks.append(current)
            current = []

    if current:
        chunks.append(current)

    return chunks


if __name__ == "__main__":
    text = sys.stdin.read().strip().splitlines()

    # Prefer heading-based split if headings are present
    has_headings = any(re.match(r'^##\s+', line) for line in text)
    if has_headings:
        chunks = split_by_headings(text)
    else:
        chunks = split_by_line_count(text)

    for i, chunk in enumerate(chunks, 1):
        print(f"## Diagram {i}")
        print("\n".join(chunk))
        print()
