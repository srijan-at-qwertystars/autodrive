from __future__ import annotations

import html
import json

from .models import AuditReport, Finding


def render_report(report: AuditReport, output_format: str) -> str:
    if output_format == "json":
        return json.dumps(report.to_dict(), indent=2, sort_keys=True)
    if output_format == "html":
        return _render_html_report(report)
    return _render_text_report(report)


def _render_text_report(report: AuditReport) -> str:
    lines = [
        f"Target: {report.target}",
        f"Docs scanned: {len(report.facts.doc_files)}",
        f"Instructions parsed: {len(report.instructions)}",
        f"Findings: {len(report.findings)}",
    ]
    for finding in report.findings:
        lines.append(
            f"- {finding.severity.upper()} {finding.kind}{_format_location(finding.source_path, finding.line)}: {finding.message}"
        )
    return "\n".join(lines)


def _render_html_report(report: AuditReport) -> str:
    findings_markup = "".join(_render_finding(finding) for finding in report.findings) or (
        '<tr><td colspan="5">No findings.</td></tr>'
    )
    doc_items = "".join(f"<li><code>{html.escape(path)}</code></li>" for path in sorted(report.facts.doc_files)) or "<li>None</li>"
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>README Reality Check Report</title>
  <style>
    :root {{
      color-scheme: light dark;
      font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    body {{
      margin: 0;
      padding: 2rem;
      line-height: 1.5;
      background: #f7f7f8;
      color: #171717;
    }}
    main {{
      max-width: 1100px;
      margin: 0 auto;
      background: #fff;
      border-radius: 12px;
      padding: 2rem;
      box-shadow: 0 12px 30px rgba(0, 0, 0, 0.08);
    }}
    h1, h2 {{
      margin-top: 0;
    }}
    .summary {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 1rem;
      margin: 1.5rem 0 2rem;
    }}
    .card {{
      border: 1px solid #d4d4d8;
      border-radius: 10px;
      padding: 1rem;
      background: #fafafa;
    }}
    .card strong {{
      display: block;
      font-size: 1.5rem;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 1rem;
    }}
    th, td {{
      border: 1px solid #d4d4d8;
      padding: 0.75rem;
      vertical-align: top;
      text-align: left;
    }}
    th {{
      background: #f4f4f5;
    }}
    .severity {{
      font-weight: 700;
      text-transform: uppercase;
    }}
    .severity-error {{
      color: #b91c1c;
    }}
    .severity-warning {{
      color: #a16207;
    }}
    code {{
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }}
    ul {{
      padding-left: 1.25rem;
    }}
  </style>
</head>
<body>
  <main>
    <h1>README Reality Check Report</h1>
    <p><strong>Target:</strong> <code>{target}</code></p>
    <section class="summary">
      <div class="card"><span>Docs scanned</span><strong>{doc_count}</strong></div>
      <div class="card"><span>Instructions parsed</span><strong>{instruction_count}</strong></div>
      <div class="card"><span>Findings</span><strong>{finding_count}</strong></div>
    </section>
    <section>
      <h2>Documentation files</h2>
      <ul>{doc_items}</ul>
    </section>
    <section>
      <h2>Findings</h2>
      <table>
        <thead>
          <tr>
            <th>Severity</th>
            <th>Kind</th>
            <th>Location</th>
            <th>Command</th>
            <th>Message</th>
          </tr>
        </thead>
        <tbody>
          {findings_markup}
        </tbody>
      </table>
    </section>
  </main>
</body>
</html>""".format(
        target=html.escape(report.target),
        doc_count=len(report.facts.doc_files),
        instruction_count=len(report.instructions),
        finding_count=len(report.findings),
        doc_items=doc_items,
        findings_markup=findings_markup,
    )


def _render_finding(finding: Finding) -> str:
    severity = html.escape(finding.severity)
    kind = html.escape(finding.kind)
    location = html.escape(_format_location(finding.source_path, finding.line).strip(" []")) or "&mdash;"
    command = html.escape(finding.command or "") or "&mdash;"
    message = html.escape(finding.message)
    return (
        "<tr>"
        f'<td><span class="severity severity-{severity.lower()}">{severity}</span></td>'
        f"<td>{kind}</td>"
        f"<td>{location}</td>"
        f"<td><code>{command}</code></td>"
        f"<td>{message}</td>"
        "</tr>"
    )


def _format_location(source_path: str | None, line: int | None) -> str:
    if not source_path:
        return ""
    location = source_path
    if line:
        location = f"{location}:{line}"
    return f" [{location}]"
