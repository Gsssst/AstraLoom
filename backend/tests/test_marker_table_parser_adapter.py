import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "parse_tables_marker.py"
spec = importlib.util.spec_from_file_location("parse_tables_marker", SCRIPT_PATH)
parse_tables_marker = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(parse_tables_marker)


def test_normalize_marker_payload_extracts_rows_cells_and_html():
    payload = {
        "tables": [
            {
                "page": 3,
                "caption": "Table 3. RULER",
                "cells": [
                    {"row": 0, "col": 0, "text": "Task"},
                    {"row": 0, "col": 1, "text": "Score"},
                    {"row": 1, "col": 0, "text": "GSM8K strict"},
                    {"row": 1, "col": 1, "text": "72.4"},
                ],
            },
            {
                "page": 4,
                "html": "<table><tr><th>Model</th><th>PG-19</th></tr><tr><td>Ours</td><td>8.2</td></tr></table>",
            },
        ]
    }

    normalized = parse_tables_marker.normalize_marker_payload(payload)

    assert len(normalized["tables"]) == 2
    assert normalized["tables"][0]["rows"] == [["Task", "Score"], ["GSM8K strict", "72.4"]]
    assert normalized["tables"][0]["cells"][0]["text"] == "Task"
    assert normalized["tables"][1]["rows"] == [["Model", "PG-19"], ["Ours", "8.2"]]


def test_normalize_marker_payload_handles_nested_pages_and_markdown():
    payload = {
        "pages": [
            {
                "page": 5,
                "children": [
                    {
                        "type": "table",
                        "markdown": "| Dataset | EM |\n| --- | --- |\n| COQA | 81.1 |",
                    }
                ],
            }
        ]
    }

    normalized = parse_tables_marker.normalize_marker_payload(payload)

    assert normalized["tables"][0]["page"] == 5
    assert normalized["tables"][0]["rows"] == [["Dataset", "EM"], ["COQA", "81.1"]]


def test_run_marker_missing_cli_has_actionable_error(monkeypatch):
    monkeypatch.setattr(parse_tables_marker.shutil, "which", lambda _name: None)

    try:
        parse_tables_marker.run_marker("/tmp/missing.pdf")
    except RuntimeError as exc:
        message = str(exc)
    else:
        raise AssertionError("expected RuntimeError")

    assert "marker_single is not installed" in message
    assert "PDF_TABLE_PARSER_COMMAND" in message
