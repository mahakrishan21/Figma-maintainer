#!/usr/bin/env python3
"""A compact outline of a Figma frame from the REST API (read-only), instead of get_metadata on a large frame.

  figma_outline.py --file <key> --node <id> [--depth 3] [--text "words"] [--type TEXT] [--ids a,b] [--save <json>]

Prints one line per layer: id, type, name, box relative to the frame, font for text, and the text itself;
capped like fm_query.py (--max, default 4000 characters). --save keeps the full JSON on disk so later
questions go to `fm_query.py nodes <json> …` without another API call.
"""
import argparse, json, os, sys, tempfile
from pathlib import Path

HERE = Path(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, str(HERE))
from figma_common import get, token  # noqa: E402
import fm_query  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--file", required=True); ap.add_argument("--node", required=True)
    ap.add_argument("--depth", type=int, default=3); ap.add_argument("--text"); ap.add_argument("--type"); ap.add_argument("--ids")
    ap.add_argument("--save"); ap.add_argument("--max", type=int, default=4000)
    a = ap.parse_args()
    node = a.node.replace("-", ":")
    data = get(f"/files/{a.file}/nodes?ids={node}&depth={a.depth + 1}", token())
    if not (data.get("nodes") or {}).get(node):
        sys.exit(f"Node {node} not found in file {a.file}")
    path = Path(a.save) if a.save else Path(tempfile.mkstemp(suffix=".json")[1])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))
    q = argparse.Namespace(path=str(path), root=node, ids=a.ids, text=a.text, type=a.type, depth=a.depth)
    fm_query.q_nodes(q, fm_query.Out(a.max))
    if a.save:
        print(f"(full JSON: {path}; ask more with fm_query.py nodes {path} --root {node} …)")
    else:
        path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
