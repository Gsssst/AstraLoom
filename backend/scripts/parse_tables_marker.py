#!/usr/bin/env python3
"""Marker table parser adapter for PDF table repair.

Outputs JSON in the high-fidelity table repair contract:
{"tables": [{"page": 1, "caption": "...", "rows": [["A", "B"], ...]}]}
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


class HtmlTableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[list[str]] = []
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "tr":
            self._row = []
        elif tag.lower() in {"td", "th"} and self._row is not None:
            self._cell = []

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        if lowered in {"td", "th"} and self._row is not None and self._cell is not None:
            self._row.append(re.sub(r"\s+", " ", "".join(self._cell)).strip())
            self._cell = None
        elif lowered == "tr" and self._row is not None:
            if any(cell.strip() for cell in self._row):
                self.rows.append(self._row)
            self._row = None


def html_to_rows(html: str) -> list[list[str]]:
    parser = HtmlTableParser()
    try:
        parser.feed(html or "")
    except Exception:
        return []
    return parser.rows


def markdown_to_rows(markdown: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in (markdown or "").splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if cells and all(re.fullmatch(r"-{3,}:?", cell.replace(" ", "")) for cell in cells):
            continue
        if any(cells):
            rows.append(cells)
    return rows


def normalize_rows(value: Any) -> list[list[str]]:
    if not isinstance(value, list):
        return []
    rows: list[list[str]] = []
    for row in value:
        cells = row.get("cells") if isinstance(row, dict) else row
        if not isinstance(cells, list):
            continue
        normalized = []
        for cell in cells:
            if isinstance(cell, dict):
                normalized.append(str(cell.get("text") or cell.get("value") or cell.get("content") or "").strip())
            else:
                normalized.append(str(cell or "").strip())
        if any(normalized):
            rows.append(normalized)
    return rows


def normalize_cells(value: Any) -> tuple[list[list[str]], list[dict[str, Any]]]:
    if not isinstance(value, list):
        return [], []
    if value and all(isinstance(item, list) for item in value):
        return normalize_rows(value), []
    positioned: dict[int, dict[int, str]] = {}
    objects: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        objects.append(item)
        row = item.get("row") if item.get("row") is not None else item.get("row_index")
        col = item.get("col") if item.get("col") is not None else item.get("col_index")
        if not isinstance(row, int) or not isinstance(col, int):
            continue
        positioned.setdefault(row, {})[col] = str(item.get("text") or item.get("value") or item.get("content") or "").strip()
    rows: list[list[str]] = []
    for row_index in sorted(positioned):
        cols = positioned[row_index]
        max_col = max(cols) if cols else -1
        row = [cols.get(col_index, "") for col_index in range(max_col + 1)]
        if any(row):
            rows.append(row)
    return rows, objects


def table_rows_from_item(item: dict[str, Any]) -> tuple[list[list[str]], list[dict[str, Any]]]:
    for key in ("rows", "table", "data"):
        rows = normalize_rows(item.get(key))
        if rows:
            return rows, []
    rows, cell_objects = normalize_cells(item.get("cells"))
    if rows:
        return rows, cell_objects
    html = item.get("html") or item.get("table_html")
    if isinstance(html, str):
        rows = html_to_rows(html)
        if rows:
            return rows, []
    markdown = item.get("markdown") or item.get("text")
    if isinstance(markdown, str):
        rows = markdown_to_rows(markdown)
        if rows:
            return rows, []
    return [], []


def iter_items(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("tables", "blocks", "children", "items", "elements", "chunks"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    pages = payload.get("pages")
    items: list[dict[str, Any]] = []
    if isinstance(pages, list):
        for index, page in enumerate(pages, 1):
            if not isinstance(page, dict):
                continue
            page_no = page.get("page") or page.get("page_number") or index
            for block in page.get("blocks") or page.get("children") or []:
                if isinstance(block, dict):
                    merged = dict(block)
                    merged.setdefault("page", page_no)
                    items.append(merged)
    return items


def normalize_marker_payload(payload: Any) -> dict[str, Any]:
    tables: list[dict[str, Any]] = []
    for index, item in enumerate(iter_items(payload), 1):
        raw_type = str(item.get("type") or item.get("block_type") or item.get("category") or item.get("label") or "").lower()
        rows, cell_objects = table_rows_from_item(item)
        if not rows and "table" not in raw_type:
            continue
        if not rows:
            continue
        table: dict[str, Any] = {
            "page": item.get("page") or item.get("page_number") or item.get("page_id"),
            "caption": item.get("caption") or item.get("title") or "",
            "rows": rows,
            "table_index": item.get("table_index") or item.get("index") or index,
        }
        confidence = item.get("confidence") or item.get("score")
        if confidence is not None:
            table["confidence"] = confidence
        bbox = item.get("bbox") or item.get("polygon")
        if bbox is not None:
            table["bbox"] = bbox
        if cell_objects:
            table["cells"] = cell_objects
        tables.append(table)
    return {"tables": tables}


def load_json_files(output_dir: Path) -> list[Any]:
    payloads: list[Any] = []
    for path in output_dir.rglob("*.json"):
        try:
            payloads.append(json.loads(path.read_text(encoding="utf-8")))
        except Exception:
            continue
    return payloads


def run_marker(pdf_path: str, *, use_llm: bool = False, timeout: int = 300) -> dict[str, Any]:
    marker_single = shutil.which("marker_single")
    if not marker_single:
        raise RuntimeError(
            "marker_single is not installed. Install Marker in the backend environment, "
            "then set PDF_TABLE_PARSER_COMMAND=\"python /app/scripts/parse_tables_marker.py --json {pdf_path}\"."
        )
    with tempfile.TemporaryDirectory(prefix="marker-table-") as tmp:
        output_dir = Path(tmp)
        cmd = [
            marker_single,
            pdf_path,
            "--output_dir",
            str(output_dir),
            "--output_format",
            "json",
            "--converter_cls",
            "marker.converters.table.TableConverter",
        ]
        if use_llm:
            cmd.append("--use_llm")
        completed = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=dict(os.environ),
        )
        if completed.returncode != 0:
            raise RuntimeError((completed.stderr or completed.stdout or "marker_single failed").strip()[:1000])
        combined: dict[str, Any] = {"tables": []}
        for payload in load_json_files(output_dir):
            normalized = normalize_marker_payload(payload)
            combined["tables"].extend(normalized["tables"])
        if not combined["tables"]:
            stdout_payload = None
            try:
                stdout_payload = json.loads(completed.stdout)
            except Exception:
                stdout_payload = None
            if stdout_payload is not None:
                combined = normalize_marker_payload(stdout_payload)
        return combined


def main() -> int:
    parser = argparse.ArgumentParser(description="Parse PDF tables with Marker and emit repair JSON.")
    parser.add_argument("pdf_path")
    parser.add_argument("--json", action="store_true", help="Emit JSON; kept for command readability.")
    parser.add_argument("--use-llm", action="store_true", help="Pass --use_llm to Marker.")
    parser.add_argument("--timeout", type=int, default=300)
    args = parser.parse_args()

    if not Path(args.pdf_path).exists():
        print(f"PDF not found: {args.pdf_path}", file=sys.stderr)
        return 2
    try:
        payload = run_marker(args.pdf_path, use_llm=args.use_llm, timeout=args.timeout)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
