"""Render diagram files offline.

Supported inputs:
- Markdown outline (.md): rendered as a Graphviz radial tree using twopi
- Graphviz DOT (.dot): rendered with dot / twopi / neato
- D2 (.d2): rendered with local d2 binary if available
- Mermaid (.mmd/.mermaid): rendered with mmdc if available, otherwise offline HTML fallback

The script is designed for offline Docker environments.
No CDN or external network access is required.
"""
from __future__ import annotations

import argparse
import base64
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


# -------------------------
# Utilities
# -------------------------

def which(cmd: str) -> str | None:
    return shutil.which(cmd)


def read_text(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def write_text(path: str, content: str) -> None:
    Path(path).write_text(content, encoding="utf-8")


def safe_stem(name: str) -> str:
    stem = re.sub(r"[^\w\-\.]+", "_", name.strip())
    stem = stem.strip("._")
    return stem or "diagram"


def get_output_dir(input_path: str | None = None) -> str:
    if os.path.isdir("/output"):
        return "/output"
    if input_path:
        p = Path(input_path).resolve().parent
        test = p / ".write_test"
        try:
            test.write_text("test", encoding="utf-8")
            test.unlink()
            return str(p)
        except OSError:
            pass
    return "/tmp"


def run_cmd(cmd: list[str], timeout: int = 90) -> tuple[int, str, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return proc.returncode, proc.stdout, proc.stderr


def detect_kind_from_path(path: str) -> str:
    suffix = Path(path).suffix.lower()
    if suffix == ".md":
        return "outline"
    if suffix in {".mmd", ".mermaid"}:
        return "mermaid"
    if suffix in {".dot", ".gv"}:
        return "dot"
    if suffix == ".d2":
        return "d2"
    return "auto"


def sniff_kind(content: str) -> str:
    """Best-effort auto detection for stdin content.

    Heuristics are intentionally conservative to avoid misclassifying D2 as DOT.
    """
    first = ""
    for line in content.splitlines():
        s = line.strip()
        if s:
            first = s
            break
    if not first:
        return "outline"

    if first.startswith(("#", "##", "###")):
        return "outline"

    if first.startswith(("mindmap", "flowchart", "sequenceDiagram", "timeline")):
        return "mermaid"

    if first.startswith(("digraph", "graph ")):
        return "dot"

    # D2 commonly uses colon-based declarations or compact relations.
    if ":" in content and "->" in content:
        return "d2"

    # Fallback: if it looks like a relation-heavy graph and has no heading syntax,
    # prefer D2 for stdin because it is more permissive than DOT.
    if "->" in content or "--" in content:
        return "d2"

    return "outline"


OUTLINE_KEYWORDS = {
    "总结", "汇报", "复盘", "笔记", "思路", "框架", "结构", "脑图", "思维导图",
    "项目", "计划", "方案", "结论", "目标", "后续", "内容", "章节", "提纲",
}
FLOW_KEYWORDS = {
    "流程", "步骤", "判断", "分支", "条件", "开始", "结束", "处理", "审批",
    "执行", "输入", "输出", "决策", "循环", "回退", "retry", "start", "end",
}
ARCH_KEYWORDS = {
    "架构", "系统", "服务", "模块", "组件", "接口", "网关", "数据库", "缓存",
    "消息队列", "调用", "依赖", "部署", "客户端", "服务端", "API", "controller",
    "service", "gateway", "database", "cache", "component", "module", "system",
}
SEQUENCE_KEYWORDS = {
    "sequenceDiagram", "participant", "actor", "autonumber", "请求", "响应", "调用顺序",
}
TIMELINE_KEYWORDS = {
    "timeline", "时间线", "里程碑", "阶段", "日期", "月份", "季度", "Q1", "Q2", "Q3", "Q4",
}


def parse_outline_nodes(text: str) -> list[tuple[int, str]]:
    """Parse headings and list items into (level, title) nodes."""
    nodes: list[tuple[int, str]] = []
    for raw in text.splitlines():
        line = raw.rstrip()
        stripped = line.lstrip()
        if not stripped:
            continue

        if stripped.startswith("#"):
            hashes = len(stripped) - len(stripped.lstrip("#"))
            title = stripped[hashes:].strip()
            if title:
                nodes.append((hashes, title))
            continue

        m = re.match(r"^(\s*)[-*]\s+(.+)$", line)
        if m:
            indent = len(m.group(1))
            title = m.group(2).strip()
            level = 2 + indent // 2
            if title:
                nodes.append((level, title))
    return nodes


def outline_stats(text: str) -> tuple[int, int, int]:
    nodes = parse_outline_nodes(text)
    if not nodes:
        return 0, 0, 0
    total = len(nodes)
    max_depth = max(level for level, _ in nodes)
    top_level = sum(1 for level, _ in nodes if level == 2)
    return total, max_depth, top_level


def outline_to_mermaid_code(text: str) -> str:
    nodes = parse_outline_nodes(text)
    if not nodes:
        return "mindmap\n  root((Topic))"

    root_title = nodes[0][1].strip()
    root_title = root_title.replace("(", "（").replace(")", "）")
    out = ["mindmap", f"  root(({root_title}))"]

    min_level = min(level for level, _ in nodes[1:]) if len(nodes) > 1 else 2
    for level, title in nodes[1:]:
        relative_depth = max(1, level - min_level + 1)
        indent = "  " * (relative_depth + 1)
        safe_title = title.replace("(", "（").replace(")", "）")
        out.append(f"{indent}{safe_title}")
    return "\n".join(out)


def looks_like_dot(content: str) -> bool:
    first = next((line.strip() for line in content.splitlines() if line.strip()), "")
    if first.startswith(("digraph", "graph ")):
        return True
    markers = [
        "->", "--", "[label=", "subgraph", "rankdir", "shape=", "style=", "cluster",
        "node [", "edge [", "graph [",
    ]
    return any(m in content for m in markers)


def looks_like_d2(content: str) -> bool:
    first = next((line.strip() for line in content.splitlines() if line.strip()), "")
    if first.startswith(("mindmap", "flowchart", "sequenceDiagram", "timeline")):
        return False
    if "->" not in content and ":" not in content:
        return False
    d2_markers = [
        ":", "style:", "shape:", "direction:", "near:", "width:", "height:",
        "fill:", "stroke:", "font:", "shadow:", "label:",
    ]
    colon_lines = sum(1 for line in content.splitlines() if re.match(r"^\s*[\w\-]+\s*:\s*.+$", line))
    arrow_lines = sum(1 for line in content.splitlines() if "->" in line or "--" in line)
    if colon_lines >= 1:
        return True
    if arrow_lines >= 2 and any(m in content for m in d2_markers):
        return True
    return False


def looks_like_mermaid(content: str) -> bool:
    first = next((line.strip() for line in content.splitlines() if line.strip()), "")
    return first.startswith(("mindmap", "flowchart", "sequenceDiagram", "timeline", "gantt", "classDiagram", "stateDiagram"))


def looks_like_sequence(content: str) -> bool:
    lower = content.lower()
    return any(k.lower() in lower for k in SEQUENCE_KEYWORDS) or "->>" in content or "-->>" in content


def looks_like_timeline(content: str) -> bool:
    lower = content.lower()
    if any(k.lower() in lower for k in TIMELINE_KEYWORDS):
        return True
    return bool(re.search(r"\b(19|20)\d{2}\b", content)) and any(tok in lower for tok in ["阶段", "phase", "milestone", "timeline", "里程碑"])


def count_keywords(text: str, keywords: set[str]) -> int:
    lower = text.lower()
    return sum(1 for k in keywords if k.lower() in lower)


def tool_available(name: str) -> bool:
    return which(name) is not None


def detect_semantic_kind(text: str) -> str:
    """Infer the diagram intent from plain text when kind is auto."""
    if looks_like_mermaid(text):
        first = next((line.strip() for line in text.splitlines() if line.strip()), "")
        if first.startswith("mindmap"):
            return "outline"
        if first.startswith(("flowchart", "gantt")):
            return "flowchart"
        if first.startswith("sequenceDiagram"):
            return "sequence"
        if first.startswith("timeline"):
            return "timeline"
        return "mermaid"

    if looks_like_sequence(text):
        return "sequence"

    if looks_like_timeline(text):
        return "timeline"

    outline_nodes = parse_outline_nodes(text)
    if outline_nodes:
        total, max_depth, top_level = outline_stats(text)
        if total >= 2 and not looks_like_dot(text) and not looks_like_d2(text):
            return "outline"

    lower = text.lower()
    arch_score = count_keywords(text, ARCH_KEYWORDS)
    flow_score = count_keywords(text, FLOW_KEYWORDS)

    if arch_score >= 2 and ("->" in text or ":" in text or "subgraph" in lower):
        return "architecture"
    if flow_score >= 2 and ("->" in text or "if" in lower or "yes" in lower or "no" in lower):
        return "flowchart"

    if looks_like_dot(text):
        return "flowchart"
    if looks_like_d2(text):
        return "architecture" if arch_score >= flow_score else "flowchart"

    if "->" in text or "--" in text:
        return "flowchart"

    return "outline"


def choose_backend(semantic_kind: str, text: str) -> tuple[str, str]:
    """Return (backend, render_hint). Backend is graphviz | d2 | mermaid."""
    kind = semantic_kind.lower()

    has_graphviz = tool_available("dot")
    has_d2 = tool_available("d2")
    has_mermaid = tool_available("mmdc")

    def prefer(*candidates: tuple[str, str]) -> tuple[str, str]:
        for backend, hint in candidates:
            if backend == "graphviz" and has_graphviz:
                return backend, hint
            if backend == "d2" and has_d2:
                return backend, hint
            if backend == "mermaid" and has_mermaid:
                return backend, hint
        # Hard fallback order if a preferred backend is missing.
        if has_graphviz:
            return "graphviz", candidates[0][1]
        if has_d2:
            return "d2", candidates[0][1]
        return "mermaid", candidates[0][1]

    if kind == "outline":
        total, max_depth, top_level = outline_stats(text)
        if total and total <= 14 and max_depth <= 4 and top_level <= 6:
            return prefer(("mermaid", "mindmap"), ("graphviz", "twopi"))
        return prefer(("graphviz", "twopi"), ("mermaid", "mindmap"))

    if kind in {"sequence", "timeline", "mermaid"}:
        return prefer(("mermaid", kind), ("graphviz", "dot"), ("d2", kind))

    arch_score = count_keywords(text, ARCH_KEYWORDS)
    flow_score = count_keywords(text, FLOW_KEYWORDS)
    dot_like = looks_like_dot(text)
    d2_like = looks_like_d2(text)

    if dot_like and not d2_like:
        return prefer(("graphviz", "dot"), ("d2", kind), ("mermaid", "flowchart"))
    if d2_like and not dot_like:
        return prefer(("d2", kind), ("graphviz", "dot"), ("mermaid", "flowchart"))

    if kind == "architecture":
        if d2_like or arch_score >= 2:
            return prefer(("d2", kind), ("graphviz", "dot"), ("mermaid", "flowchart"))
        return prefer(("graphviz", "dot"), ("d2", kind), ("mermaid", "flowchart"))

    if kind == "flowchart":
        if d2_like or flow_score >= 2 or ":" in text:
            return prefer(("d2", kind), ("graphviz", "dot"), ("mermaid", "flowchart"))
        if dot_like or ("subgraph" in text.lower()) or ("rankdir" in text.lower()):
            return prefer(("graphviz", "dot"), ("d2", kind), ("mermaid", "flowchart"))
        return prefer(("mermaid", "flowchart"), ("d2", kind), ("graphviz", "dot"))

    if d2_like:
        return prefer(("d2", kind), ("graphviz", "dot"), ("mermaid", "flowchart"))
    if dot_like:
        return prefer(("graphviz", "dot"), ("d2", kind), ("mermaid", "flowchart"))
    return prefer(("mermaid", "flowchart"), ("graphviz", "dot"), ("d2", kind))


# -------------------------
# Outline -> Graphviz tree
# -------------------------

@dataclass
class OutlineNode:
    title: str
    level: int
    children: list["OutlineNode"] = field(default_factory=list)


def parse_markdown_outline(text: str) -> OutlineNode:
    """Parse Markdown headings/lists into a tree.

    Supports:
    - Headings: #, ##, ### ...
    - List items: - / * with indentation (2 spaces = 1 level)
    """
    nodes: list[tuple[int, str]] = []

    for raw in text.splitlines():
        line = raw.rstrip()
        stripped = line.lstrip()
        if not stripped:
            continue

        if stripped.startswith("#"):
            hashes = len(stripped) - len(stripped.lstrip("#"))
            title = stripped[hashes:].strip()
            if title:
                nodes.append((hashes, title))
            continue

        m = re.match(r"^(\s*)[-*]\s+(.+)$", line)
        if m:
            indent = len(m.group(1))
            title = m.group(2).strip()
            level = 2 + indent // 2
            if title:
                nodes.append((level, title))
            continue

    if not nodes:
        return OutlineNode("Topic", 1, [])

    root_level, root_title = nodes[0]
    root = OutlineNode(root_title, root_level, [])
    stack: list[OutlineNode] = [root]

    for level, title in nodes[1:]:
        node = OutlineNode(title, level, [])
        while stack and level <= stack[-1].level:
            stack.pop()
        parent = stack[-1] if stack else root
        parent.children.append(node)
        stack.append(node)

    return root


def _escape_dot(label: str) -> str:
    return label.replace("\\", "\\\\").replace('"', '\\"')


def build_dot_from_outline(root: OutlineNode) -> str:
    """Create a Graphviz DOT graph with radial layout via twopi."""
    nodes: list[tuple[str, OutlineNode, str | None]] = []
    edges: list[tuple[str, str]] = []

    def walk(node: OutlineNode, parent_id: str | None = None, depth: int = 0, counter: list[int] = [0]):
        node_id = f"n{counter[0]}"
        counter[0] += 1
        nodes.append((node_id, node, parent_id))
        if parent_id is not None:
            edges.append((parent_id, node_id))
        for child in node.children:
            walk(child, node_id, depth + 1, counter)

    walk(root)

    palette = [
        "#dbeafe", "#dcfce7", "#fef3c7", "#fce7f3", "#ede9fe", "#ffe4e6", "#cffafe"
    ]

    lines = []
    lines.append('graph G {')
    lines.append('  graph [layout=twopi, root="n0", overlap=false, splines=true, bgcolor="white", pad=0.25, ranksep=1.0];')
    lines.append('  node [shape=box, style="rounded,filled", color="#94a3b8", penwidth=1.2, fontname="Noto Sans CJK SC, Microsoft YaHei, PingFang SC, sans-serif", fontsize=13, margin="0.16,0.10"];')
    lines.append('  edge [color="#94a3b8", penwidth=1.0];')

    for idx, (node_id, node, parent_id) in enumerate(nodes):
        depth = 0
        pid = parent_id
        while pid is not None:
            depth += 1
            # find parent id's parent
            parent_tuple = next((t for t in nodes if t[0] == pid), None)
            pid = parent_tuple[2] if parent_tuple else None

        if idx == 0:
            lines.append(f'  {node_id} [label="{_escape_dot(node.title)}", fillcolor="#111827", fontcolor="white", shape=ellipse, penwidth=1.8];')
        elif depth == 1:
            fill = palette[(idx - 1) % len(palette)]
            lines.append(f'  {node_id} [label="{_escape_dot(node.title)}", fillcolor="{fill}"];')
        else:
            lines.append(f'  {node_id} [label="{_escape_dot(node.title)}", fillcolor="#ffffff"];')

    for a, b in edges:
        lines.append(f"  {a} -- {b};")

    lines.append('}')
    return "\n".join(lines)


def render_graphviz(dot_source: str, output_path: str, fmt: str, engine: str = "twopi") -> str:
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile("w", suffix=".dot", delete=False, encoding="utf-8") as f:
        tmp = f.name
        f.write(dot_source)

    try:
        cmd = [engine, f"-T{fmt}", tmp, "-o", str(out)]
        rc, _, err = run_cmd(cmd)
        if rc != 0:
            raise RuntimeError(err.strip() or f"{engine} failed")
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass

    return str(out)


def wrap_svg_html(svg_path: str, title: str, source_label: str, source_text: str | None = None) -> str:
    svg = Path(svg_path).read_text(encoding="utf-8")
    escaped_source = html.escape(source_text or "", quote=False)
    html_path = str(Path(svg_path).with_suffix(".html"))
    content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
<style>
body {{
  margin: 0;
  padding: 24px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  background: #ffffff;
  color: #111827;
}}
.container {{
  max-width: 1400px;
  margin: 0 auto;
}}
.header {{
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e5e7eb;
}}
.header h1 {{
  margin: 0;
  font-size: 18px;
  font-weight: 700;
}}
.meta {{
  margin-top: 6px;
  color: #6b7280;
  font-size: 12px;
}}
.panel {{
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 20px;
  background: #fafafa;
  overflow: auto;
}}
details {{
  margin-top: 16px;
}}
summary {{
  cursor: pointer;
  color: #4b5563;
  font-size: 13px;
  font-weight: 600;
}}
pre {{
  white-space: pre-wrap;
  word-break: break-word;
  padding: 12px;
  background: #f8fafc;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  font-size: 12px;
  line-height: 1.5;
}}
svg {{
  max-width: 100%;
  height: auto;
}}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>{html.escape(title)}</h1>
    <div class="meta">Source: {html.escape(source_label)} · Offline Graphviz render</div>
  </div>
  <div class="panel">
    {svg}
  </div>
  <details>
    <summary>View source</summary>
    <pre>{escaped_source}</pre>
  </details>
</div>
</body>
</html>"""
    Path(html_path).write_text(content, encoding="utf-8")
    return html_path


# -------------------------
# Mermaid rendering
# -------------------------

MERMAID_LOCAL_PATHS = [
    "/usr/local/share/mermaid/mermaid.min.js",
    "/usr/local/lib/node_modules/@mermaid-js/mermaid-cli/node_modules/@mermaid-js/mermaid/dist/mermaid.min.js",
]


def find_local_mermaid_js() -> str | None:
    for p in MERMAID_LOCAL_PATHS:
        if os.path.isfile(p):
            return p
    return None


def build_mermaid_html(code: str, title: str, source_label: str) -> str:
    js_path = find_local_mermaid_js()
    escaped_code = html.escape(code, quote=False)
    escaped_src = html.escape(code, quote=False)

    if js_path:
        js = Path(js_path).read_text(encoding="utf-8")
        mermaid_block = f"<script>\n{js}\n</script>\n<script>\nmermaid.initialize({{ startOnLoad: true, theme: 'default', securityLevel: 'loose', flowchart: {{ useMaxWidth: true, htmlLabels: true, curve: 'basis' }}, mindmap: {{ useMaxWidth: true }}, sequence: {{ useMaxWidth: true }}, timeline: {{ useMaxWidth: true }} }});\n</script>"
    else:
        mermaid_block = ""

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
<style>
body {{
  margin: 0;
  padding: 24px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  background: white;
}}
.container {{
  max-width: 1400px;
  margin: 0 auto;
}}
.header {{
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e5e7eb;
}}
.header h1 {{
  margin: 0;
  font-size: 18px;
  font-weight: 700;
}}
.meta {{
  margin-top: 6px;
  color: #6b7280;
  font-size: 12px;
}}
.panel {{
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 16px;
  background: #fafafa;
  overflow: auto;
}}
pre.mermaid {{
  background: white;
  padding: 8px;
  border-radius: 8px;
}}
details {{
  margin-top: 16px;
}}
summary {{
  cursor: pointer;
  color: #4b5563;
  font-size: 13px;
  font-weight: 600;
}}
pre {{
  white-space: pre-wrap;
  word-break: break-word;
  padding: 12px;
  background: #f8fafc;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  font-size: 12px;
  line-height: 1.5;
}}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>{html.escape(title)}</h1>
    <div class="meta">Source: {html.escape(source_label)} · Offline Mermaid preview</div>
  </div>
  <div class="panel">
    <pre class="mermaid">{escaped_code}</pre>
  </div>
  <details>
    <summary>View source</summary>
    <pre>{escaped_src}</pre>
  </details>
</div>
{mermaid_block}
</body>
</html>"""


def render_mermaid(code: str, output_path: str, fmt: str, title: str, source_label: str) -> str:
    if fmt == "html":
        html_path = output_path
        Path(html_path).write_text(build_mermaid_html(code, title, source_label), encoding="utf-8")
        return html_path

    mmdc = which("mmdc")
    if mmdc:
        with tempfile.NamedTemporaryFile("w", suffix=".mmd", delete=False, encoding="utf-8") as f:
            tmp = f.name
            f.write(code.strip())
        try:
            cmd = [
                mmdc,
                "-p", "/etc/mermaid-cli/puppeteer-config.json",
                "-i", tmp,
                "-o", output_path,
                "-w", "1600",
                "-b", "white",
            ]
            rc, _, err = run_cmd(cmd, timeout=120)
            if rc != 0:
                raise RuntimeError(err.strip() or "mmdc failed")
        finally:
            try:
                os.unlink(tmp)
            except OSError:
                pass
        return output_path

    # Offline HTML fallback
    html_path = Path(output_path).with_suffix(".html")
    html_path.write_text(build_mermaid_html(code, title, source_label), encoding="utf-8")
    return str(html_path)


# -------------------------
# D2 rendering
# -------------------------

def render_d2(code: str, output_path: str, fmt: str) -> str:
    d2 = which("d2")
    if not d2:
        html_path = Path(output_path).with_suffix(".html")
        html_path.write_text(f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><title>D2 unavailable</title></head>
<body>
<pre>{html.escape(code)}</pre>
<p>本地未找到 d2，可先查看源码。</p>
</body>
</html>""", encoding="utf-8")
        return str(html_path)

    with tempfile.NamedTemporaryFile("w", suffix=".d2", delete=False, encoding="utf-8") as f:
        tmp = f.name
        f.write(code.strip())
    try:
        cmd = [d2, tmp, output_path]
        rc, _, err = run_cmd(cmd, timeout=120)
        if rc != 0:
            raise RuntimeError(err.strip() or "d2 failed")
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass
    return output_path


# -------------------------
# DOT rendering
# -------------------------

def render_dot(code: str, output_path: str, fmt: str) -> str:
    engine = "dot"
    with tempfile.NamedTemporaryFile("w", suffix=".dot", delete=False, encoding="utf-8") as f:
        tmp = f.name
        f.write(code.strip())
    try:
        cmd = [engine, f"-T{fmt}", tmp, "-o", output_path]
        rc, _, err = run_cmd(cmd, timeout=120)
        if rc != 0:
            raise RuntimeError(err.strip() or "dot failed")
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass
    return output_path


# -------------------------
# Main render logic
# -------------------------

def render_outline(text: str, output_path: str, fmt: str, title: str, source_label: str, backend: str = "graphviz") -> str:
    if backend == "mermaid":
        mermaid_code = outline_to_mermaid_code(text)
        return render_mermaid(mermaid_code, output_path, fmt, title, source_label)

    root = parse_markdown_outline(text)
    dot_source = build_dot_from_outline(root)

    if fmt == "html":
        svg_path = Path(output_path).with_suffix(".svg")
        render_graphviz(dot_source, str(svg_path), "svg", engine="twopi")
        return wrap_svg_html(str(svg_path), title, source_label, text)

    if fmt not in {"svg", "png"}:
        fmt = "svg"
    return render_graphviz(dot_source, output_path, fmt, engine="twopi")


def render_from_kind(kind: str, text: str, output_path: str, fmt: str, title: str, source_label: str) -> str:
    kind = kind.lower()

    if kind == "outline":
        backend, _hint = choose_backend(kind, text)
        return render_outline(text, output_path, fmt, title, source_label, backend=backend)

    if kind == "dot":
        if fmt == "html":
            svg_path = Path(output_path).with_suffix(".svg")
            render_dot(text, str(svg_path), "svg")
            return wrap_svg_html(str(svg_path), title, source_label, text)
        if fmt not in {"svg", "png"}:
            fmt = "svg"
        return render_dot(text, output_path, fmt)

    if kind == "d2":
        if fmt == "html":
            svg_path = Path(output_path).with_suffix(".svg")
            render_d2(text, str(svg_path), "svg")
            if str(svg_path).endswith(".svg") and Path(svg_path).exists():
                return wrap_svg_html(str(svg_path), title, source_label, text)
            return str(Path(output_path).with_suffix(".html"))
        if fmt not in {"svg", "png"}:
            fmt = "svg"
        return render_d2(text, output_path, fmt)

    if kind == "mermaid":
        return render_mermaid(text, output_path, fmt, title, source_label)

    semantic_kind = detect_semantic_kind(text)
    backend, _hint = choose_backend(semantic_kind, text)

    if semantic_kind == "outline":
        return render_outline(text, output_path, fmt, title, source_label, backend=backend)

    if backend == "graphviz":
        if fmt == "html":
            svg_path = Path(output_path).with_suffix(".svg")
            render_dot(text, str(svg_path), "svg")
            return wrap_svg_html(str(svg_path), title, source_label, text)
        if fmt not in {"svg", "png"}:
            fmt = "svg"
        return render_dot(text, output_path, fmt)

    if backend == "d2":
        if fmt == "html":
            svg_path = Path(output_path).with_suffix(".svg")
            render_d2(text, str(svg_path), "svg")
            if Path(svg_path).exists():
                return wrap_svg_html(str(svg_path), title, source_label, text)
            return str(Path(output_path).with_suffix(".html"))
        if fmt not in {"svg", "png"}:
            fmt = "svg"
        return render_d2(text, output_path, fmt)

    if semantic_kind in {"sequence", "timeline"}:
        return render_mermaid(text, output_path, fmt, title, source_label)

    if semantic_kind == "mermaid":
        return render_mermaid(text, output_path, fmt, title, source_label)

    if semantic_kind in {"flowchart", "architecture"} and backend == "mermaid":
        if semantic_kind == "flowchart" and not looks_like_mermaid(text):
            mermaid_code = "flowchart TD\n" + "\n".join(f"    {line}" for line in text.splitlines())
        else:
            mermaid_code = text
        return render_mermaid(mermaid_code, output_path, fmt, title, source_label)

    return render_mermaid(text, output_path, fmt, title, source_label)


def output_result(path: str, fmt: str, kind: str) -> None:
    result: dict[str, object] = {
        "output_file": path,
        "format": fmt,
        "kind": kind,
    }
    if Path(path).is_file():
        if fmt in {"png", "svg"}:
            data = Path(path).read_bytes()
            result["size_bytes"] = len(data)
            result["base64"] = base64.b64encode(data).decode("ascii")
        else:
            try:
                result["content"] = Path(path).read_text(encoding="utf-8")
            except Exception:
                pass
            result["size_bytes"] = Path(path).stat().st_size
    print(json.dumps(result, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Render diagrams offline from .md/.dot/.d2/.mmd inputs.")
    parser.add_argument("input", nargs="?", default=None, help="Path to input file.")
    parser.add_argument("--stdin", action="store_true", help="Read content from stdin.")
    parser.add_argument("--name", default="diagram", help="Base name for output files when using --stdin.")
    parser.add_argument("--kind", default="auto", choices=["auto", "outline", "dot", "d2", "mermaid"], help="Explicit input kind.")
    parser.add_argument("-o", "--output", default=None, help="Output file path.")
    parser.add_argument("-f", "--format", default=None, choices=["png", "svg", "html"], help="Output format.")
    args = parser.parse_args()

    if args.stdin:
        text = sys.stdin.read()
        if not text.strip():
            print("Error: No content received from stdin", file=sys.stderr)
            sys.exit(1)
        title = args.name
        source_label = f"{args.name}.txt"
        input_kind = args.kind
    elif args.input:
        path = Path(args.input)
        if not path.is_file():
            print(f"Error: input file not found: {args.input}", file=sys.stderr)
            sys.exit(1)
        text = read_text(args.input)
        title = path.stem.replace("-", " ").replace("_", " ").title()
        source_label = path.name
        input_kind = args.kind if args.kind != "auto" else detect_kind_from_path(args.input)
    else:
        parser.error("Either provide an input file or use --stdin")

    out_dir = get_output_dir(args.input if args.input else None)
    stem = safe_stem(title)

    if args.output:
        output_path = args.output
    else:
        ext = args.format or "svg"
        output_path = str(Path(out_dir) / f"{stem}.{ext}")

    if input_kind == "auto":
        input_kind = detect_semantic_kind(text)

    if args.format:
        fmt = args.format
    else:
        if input_kind in {"outline", "dot", "d2"}:
            fmt = "svg"
        elif input_kind in {"sequence", "timeline", "mermaid"}:
            fmt = "html"
        else:
            fmt = "svg"

    rendered = render_from_kind(input_kind, text, output_path, fmt, title, source_label)
    print(f"Rendered: {rendered}", file=sys.stderr)
    output_result(rendered, Path(rendered).suffix.lstrip(".") or fmt, input_kind)


if __name__ == "__main__":
    main()
