#!/usr/bin/env python3
"""Render an HTML diff report from diff-summary.json.

Input: diff-summary JSON produced by compare_sarif.py
Output: diff-report.html with a sortable table and basic styling.
No external dependencies required.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys
from html import escape


def main():
    if len(sys.argv) < 3:
        print("Usage: render_diff_html.py <diff-summary.json> <output.html>", file=sys.stderr)
        return 2
    summary_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2])
    if not summary_path.exists():
        print(f"Summary file not found: {summary_path}", file=sys.stderr)
        return 1
    data = json.loads(summary_path.read_text(encoding='utf-8'))
    counts = data.get('counts', {})
    details = data.get('details', {})

    def severity_row(label: str, c: dict) -> str:
        return (
            f"<tr><th>{escape(label)}</th>"
            f"<td>{c.get('total', 0)}</td>"
            f"<td>{c.get('error', 0)}</td>"
            f"<td>{c.get('warning', 0)}</td>"
            f"<td>{c.get('note', 0)}</td></tr>"
        )

    def render_items(kind: str):
        items = details.get(kind, [])
        rows = []
        for r in items[:500]:  # cap
            rule = escape(str(r.get('ruleId') or r.get('rule', {}).get('id') or ''))
            lvl = escape(str(r.get('level') or ''))
            msg = escape(((r.get('message') or {}).get('text') or '')[:400])
            locs = r.get('locations') or []
            if locs:
                phys = locs[0].get('physicalLocation', {})
                uri = escape(str((phys.get('artifactLocation') or {}).get('uri') or ''))
                region = phys.get('region') or {}
                line = region.get('startLine')
                column = region.get('startColumn')
                location = f"{uri}:{line}:{column}" if uri else "(no location)"
            else:
                location = "(no location)"
            rows.append(f"<tr><td>{lvl}</td><td>{rule}</td><td>{location}</td><td class='msg'>{msg}</td></tr>")
        more = ''
        if len(items) > 500:
            more = f"<p>... {len(items) - 500} more omitted</p>"
        return f"<h2>{kind.capitalize()} ({len(items)})</h2><table class='issues'><thead><tr><th>Level</th><th>Rule</th><th>Location</th><th>Message</th></tr></thead><tbody>{''.join(rows)}</tbody></table>{more}"

    html = f"""<!DOCTYPE html>
<html lang='en'>
<head>
<meta charset='utf-8'/>
<title>Static Analysis Diff Report</title>
<style>
 body {{ font-family: system-ui, Arial, sans-serif; margin: 1.2rem; background:#f9fafb; color:#111; }}
 h1 {{ margin-top:0; }}
 table.summary {{ border-collapse: collapse; margin-bottom: 2rem; }}
 table.summary th, table.summary td {{ border:1px solid #ccc; padding:4px 8px; text-align:right; }}
 table.summary th:first-child {{ text-align:left; }}
 table.issues {{ border-collapse: collapse; width:100%; margin-bottom:2rem; }}
 table.issues th, table.issues td {{ border:1px solid #ddd; padding:4px 6px; vertical-align: top; }}
 table.issues th {{ background:#f0f0f0; position:sticky; top:0; }}
 td.msg {{ max-width:600px; }}
 .badge {{ display:inline-block; padding:2px 6px; border-radius:4px; font-size:12px; font-weight:600; }}
 .level-error {{ background:#dc2626; color:#fff; }}
 .level-warning {{ background:#f59e0b; color:#111; }}
 .level-note {{ background:#3b82f6; color:#fff; }}
 .footer {{ margin-top:3rem; font-size:12px; color:#555; }}
</style>
</head>
<body>
<h1>Static Analysis Diff Report</h1>
<table class='summary'>
<thead><tr><th>Category</th><th>Total</th><th>Errors</th><th>Warnings</th><th>Notes</th></tr></thead>
<tbody>
{severity_row('New', counts.get('new', {}))}
{severity_row('Fixed', counts.get('fixed', {}))}
{severity_row('Persisted', counts.get('persisted', {}))}
</tbody>
</table>
{render_items('new')}
{render_items('fixed')}
{render_items('persisted')}
<div class='footer'>Generated from {escape(str(summary_path))}</div>
</body>
</html>"""

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding='utf-8')
    print(f"HTML report written: {out_path}")
    return 0


if __name__ == '__main__':  # pragma: no cover
    raise SystemExit(main())
