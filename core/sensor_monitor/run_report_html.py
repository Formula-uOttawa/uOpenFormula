"""Embed a common report in an offline HTML template with no dependencies."""

import json
from pathlib import Path


def render_run_report(report):
    payload = json.dumps(report, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
    # A CSV value must never terminate the JSON script element or become markup.
    for raw, escaped in (("&", "\\u0026"), ("<", "\\u003c"), (">", "\\u003e"),
                         ("\u2028", "\\u2028"), ("\u2029", "\\u2029")):
        payload = payload.replace(raw, escaped)
    template = Path(__file__).with_name("run_report_template.html").read_text(encoding="utf-8")
    return template.replace("__RUN_REPORT_JSON__", payload)
