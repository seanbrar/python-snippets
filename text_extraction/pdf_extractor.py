#!/usr/bin/env python3
"""
PDF Text Extractor

Extracts text from PDF files with structure preservation, semantic analysis
(headings, lists, code blocks), two-column layout detection, table extraction,
and optional Poppler backend support.

Use the project venv from the repo root:  .venv/bin/python text_extraction/pdf_extractor.py ...
Or activate first:  source .venv/bin/activate

Usage:
    python text_extraction/pdf_extractor.py document.pdf --semantic --dedup
    python text_extraction/pdf_extractor.py document.pdf --semantic --start 5 --end 20 -o out.md
    python text_extraction/pdf_extractor.py document.pdf --use-poppler --dedup
    python text_extraction/pdf_extractor.py document.pdf --extract-tables --tables-dir tables/

Run ``python text_extraction/pdf_extractor.py --tips`` for more examples.
"""

import os
import sys

if __name__ == "__main__":
    _script_dir = os.path.dirname(os.path.abspath(__file__))
    _repo_root = os.path.dirname(_script_dir)
    _venv_python = os.path.join(_repo_root, ".venv", "bin", "python")
    if os.path.exists(_venv_python) and os.path.realpath(
        sys.executable
    ) != os.path.realpath(_venv_python):
        os.execv(_venv_python, [_venv_python] + sys.argv)

import argparse
import csv
import re
import shutil
import subprocess
import unicodedata
from collections import Counter
from pathlib import Path
from statistics import median
from typing import Any, Dict, List, Tuple

import pdfplumber


# ---------------------------------------------------------------------------
# Shared font-analysis helper
# ---------------------------------------------------------------------------

_MONO_FONTS = frozenset({"mono", "courier", "consolas", "menlo"})
_BOLD_FONTS = frozenset({"bold", "black", "heavy", "semibold", "demi", "medium"})


def _font_fractions(fontnames: List[str]) -> Tuple[float, float]:
    """Return ``(mono_fraction, bold_fraction)`` from lowercase font-name fragments."""
    if not fontnames:
        return 0.0, 0.0
    n = len(fontnames)
    mono = sum(1 for f in fontnames if any(t in f for t in _MONO_FONTS))
    bold = sum(1 for f in fontnames if any(t in f for t in _BOLD_FONTS))
    return mono / n, bold / n


# ---------------------------------------------------------------------------
# Line grouping
# ---------------------------------------------------------------------------


def _group_words_into_lines(
    words: List[Dict[str, Any]], line_tol: float = 2.0
) -> List[Dict[str, Any]]:
    """Group word dicts into line dicts by vertical proximity.

    Each returned dict has keys: text, top, x0, x1, avg_size,
    mono_fraction, bold_fraction.
    """
    if not words:
        return []

    sorted_words = sorted(words, key=lambda w: (w.get("top", 0.0), w.get("x0", 0.0)))
    lines: List[Dict[str, Any]] = []
    current_words: List[Dict[str, Any]] = []
    current_top: float = sorted_words[0].get("top", 0.0)

    def _flush() -> None:
        if not current_words:
            return
        by_x = sorted(current_words, key=lambda w: w.get("x0", 0.0))
        text = " ".join(w.get("text", "") for w in by_x).strip()
        if not text:
            return
        x0 = min(w.get("x0", 0.0) for w in current_words)
        x1 = max(w.get("x1", 0.0) for w in current_words)
        top = min(w.get("top", 0.0) for w in current_words)
        sizes = [
            w["size"]
            for w in current_words
            if isinstance(w.get("size"), (int, float))
        ]
        avg_size = sum(sizes) / len(sizes) if sizes else None
        fontnames = [
            (w.get("fontname") or "").lower()
            for w in current_words
            if w.get("fontname")
        ]
        mono_frac, bold_frac = _font_fractions(fontnames)
        lines.append(
            {
                "text": text,
                "top": top,
                "x0": x0,
                "x1": x1,
                "avg_size": avg_size,
                "mono_fraction": mono_frac,
                "bold_fraction": bold_frac,
            }
        )

    for w in sorted_words:
        top = w.get("top", 0.0)
        if abs(top - current_top) <= line_tol:
            current_words.append(w)
        else:
            _flush()
            current_words = [w]
            current_top = top
    _flush()

    lines.sort(key=lambda ln: (ln["top"], ln["x0"]))
    return lines


def _group_chars_into_lines(
    chars: List[Dict[str, Any]],
    line_tol: float = 2.0,
    gap_scale: float = 1.0,
) -> List[Dict[str, Any]]:
    """Group character dicts into lines, reconstructing spacing from x-gaps.

    Produces the same output shape as ``_group_words_into_lines``.
    """
    if not chars:
        return []

    sorted_chars = sorted(
        chars, key=lambda c: (c.get("top", 0.0), c.get("x0", 0.0))
    )
    results: List[Dict[str, Any]] = []
    current: List[Dict[str, Any]] = []
    current_top: float = sorted_chars[0].get("top", 0.0)

    def _flush(acc: List[Dict[str, Any]]) -> None:
        if not acc:
            return
        by_x = sorted(acc, key=lambda c: c.get("x0", 0.0))
        widths = [
            float(c.get("x1", 0.0)) - float(c.get("x0", 0.0)) for c in by_x
        ]
        sizes = [
            float(c["size"])
            for c in by_x
            if isinstance(c.get("size"), (int, float))
        ]
        avg_size = (sum(sizes) / len(sizes)) if sizes else None
        widths_pos = [w for w in widths if w > 0]
        base_w = median(widths_pos) if widths_pos else 3.0
        gap_threshold = gap_scale * max(0.5 * base_w, (avg_size or 8.0) * 0.16)

        text_parts: List[str] = []
        fontnames: List[str] = []
        prev = None
        for c in by_x:
            if prev is not None:
                gap = float(c.get("x0", 0.0)) - float(prev.get("x1", 0.0))
                if gap > gap_threshold:
                    text_parts.append(" ")
            text_parts.append(c.get("text", ""))
            fn = (c.get("fontname") or "").lower()
            if fn:
                fontnames.append(fn)
            prev = c

        line_text = "".join(text_parts).strip()
        if not line_text:
            return

        x0 = min(float(c.get("x0", 0.0)) for c in by_x)
        x1 = max(float(c.get("x1", 0.0)) for c in by_x)
        top = min(float(c.get("top", 0.0)) for c in by_x)
        mono_frac, bold_frac = _font_fractions(fontnames)
        results.append(
            {
                "text": line_text,
                "top": top,
                "x0": x0,
                "x1": x1,
                "avg_size": avg_size,
                "mono_fraction": mono_frac,
                "bold_fraction": bold_frac,
            }
        )

    for c in sorted_chars:
        top = float(c.get("top", 0.0))
        if abs(top - current_top) <= line_tol:
            current.append(c)
        else:
            _flush(current)
            current = [c]
            current_top = top
    _flush(current)

    results.sort(key=lambda ln: (ln["top"], ln["x0"]))
    return results


# ---------------------------------------------------------------------------
# Column detection
# ---------------------------------------------------------------------------


def _detect_columns(lines: List[Dict[str, Any]], page_width: float) -> bool:
    """Heuristically detect a two-column layout."""
    if not lines:
        return False
    mids = [0.5 * (ln["x0"] + ln["x1"]) for ln in lines]
    left = [m for m in mids if m < page_width * 0.5]
    right = [m for m in mids if m >= page_width * 0.5]
    if len(left) < 5 or len(right) < 5:
        return False
    left_med = sorted(left)[len(left) // 2]
    right_med = sorted(right)[len(right) // 2]
    return (right_med - left_med) > (page_width * 0.2)


def _compute_column_divider(
    lines: List[Dict[str, Any]], page_width: float
) -> float:
    """Estimate the x-coordinate dividing two columns."""
    if not lines:
        return page_width * 0.5
    mids = [0.5 * (ln["x0"] + ln["x1"]) for ln in lines]
    left = [m for m in mids if m < page_width * 0.5]
    right = [m for m in mids if m >= page_width * 0.5]
    if len(left) < 5 or len(right) < 5:
        return page_width * 0.5
    left_med = sorted(left)[len(left) // 2]
    right_med = sorted(right)[len(right) // 2]
    if (right_med - left_med) <= (page_width * 0.2):
        return page_width * 0.5
    return 0.5 * (left_med + right_med)


# ---------------------------------------------------------------------------
# Semantic line classification
# ---------------------------------------------------------------------------


def _classify_line(
    ln: Dict[str, Any],
    page_median_size: float | None,
    page_width: float,
) -> Dict[str, Any]:
    """Classify a text line as heading, code, list item, or body text."""
    text = ln["text"].strip()
    xmid = 0.5 * (ln["x0"] + ln["x1"])
    avg = ln.get("avg_size")

    is_heading = False
    heading_level = 0

    if page_median_size and avg:
        ratio = avg / page_median_size
        if ratio >= 1.35 and len(text) <= 80:
            is_heading, heading_level = True, 1
        elif ratio >= 1.18 and len(text) <= 100:
            is_heading, heading_level = True, 2

    if (
        not is_heading
        and len(text) <= 120
        and ln.get("bold_fraction", 0.0) >= 0.6
        and page_median_size
        and avg
        and 0.9 <= avg / page_median_size <= 1.3
    ):
        is_heading, heading_level = True, max(heading_level, 2)

    if (
        not is_heading
        and len(text) <= 80
        and abs(xmid - page_width * 0.5) <= page_width * 0.12
        and page_median_size
        and avg
        and avg / page_median_size >= 1.1
    ):
        is_heading, heading_level = True, max(heading_level, 2)

    if is_heading:
        if re.match(r"^\s*\d+[\.)]\s+", text) or re.match(
            r"^\s*[\u2022\-\*\u25E6\u25AA]\s+", text
        ):
            is_heading, heading_level = False, 0
        elif len([w for w in text.split() if w.isalnum()]) < 2:
            is_heading, heading_level = False, 0

    is_code = ln.get("mono_fraction", 0.0) >= 0.7
    if not is_code and text:
        non_space = sum(1 for c in text if not c.isspace())
        if non_space >= 8:
            symbols = sum(1 for c in text if c in "{}[]();=<>$`~_|\\/:#%@&*+-")
            if symbols / non_space >= 0.15:
                is_code = True

    is_list = bool(
        re.match(
            r"^\s*(?:[\u2022\-\*\u25E6\u25AA]|\(?[0-9ivxIVXab]\)?[\.)])\s+",
            text,
        )
    )

    return {
        "type": "line",
        "text": text,
        "is_heading": is_heading,
        "heading_level": heading_level,
        "is_code": is_code,
        "is_list": is_list,
        "xmid": xmid,
        "top": ln["top"],
    }


# ---------------------------------------------------------------------------
# Markdown table formatting
# ---------------------------------------------------------------------------


def _format_markdown_table(rows: List[List[str]]) -> str:
    if not rows:
        return ""
    max_cols = max(len(r) for r in rows)
    norm = [r + [""] * (max_cols - len(r)) for r in rows]
    header = norm[0]
    sep = ["---"] * max_cols
    lines = [
        "| " + " | ".join(c.strip() for c in header) + " |",
        "| " + " | ".join(sep) + " |",
    ]
    for r in norm[1:]:
        lines.append("| " + " | ".join(c.strip() for c in r) + " |")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Text post-processing
# ---------------------------------------------------------------------------


def post_process_text(text: str) -> str:
    """Normalize Unicode, fix ligatures, rejoin broken words, and tidy whitespace.

    This is intentionally conservative: it only performs transformations that
    are safe across a wide range of document types.  Earlier versions
    contained aggressive heuristics (e.g. removing spaces after the letter
    'x', replacing em/en dashes with hyphens, force-joining all non-terminal
    lines) that silently mangled legitimate content.
    """
    try:
        text = unicodedata.normalize("NFKC", text)
    except Exception:
        pass

    text = text.replace("\u00a0", " ")
    text = text.replace("\u00ad", "")

    _LIGATURES = {
        "\ufb01": "fi",
        "\ufb02": "fl",
        "\ufb00": "ff",
        "\ufb03": "ffi",
        "\ufb04": "ffl",
    }
    for old, new in _LIGATURES.items():
        text = text.replace(old, new)

    text = re.sub(r"\n{3,}", "\n\n", text)

    # Rejoin hyphenated words broken across lines
    text = re.sub(r"(\w+)-\s*\n\s*(\w+)", r"\1\2", text)

    # Join continuation lines: a lowercase letter following a line that ends
    # with a lowercase letter or common continuation punctuation.
    text = re.sub(r"([a-z,;])\n([a-z])", r"\1 \2", text)

    # Clean up spacing around punctuation
    text = re.sub(r" +([.,;:)])", r"\1", text)
    text = re.sub(r"(\() +", r"\1", text)

    return text


def dedup_overlapped_text(text: str) -> str:
    """Remove doubled characters and consecutive duplicate lines."""
    lines = text.split("\n")
    cleaned: List[str] = []

    for line in lines:
        doubled = sum(
            1
            for i in range(0, len(line) - 1, 2)
            if line[i] == line[i + 1] and line[i].isalpha()
        )
        total_pairs = len(line) // 2

        if total_pairs > 3 and doubled / total_pairs > 0.7:
            deduped: List[str] = []
            i = 0
            while i < len(line):
                if (
                    i + 1 < len(line)
                    and line[i] == line[i + 1]
                    and line[i].isalpha()
                ):
                    deduped.append(line[i])
                    i += 2
                else:
                    deduped.append(line[i])
                    i += 1
            cleaned.append("".join(deduped))
        else:
            cleaned.append(line)

    final: List[str] = []
    prev = None
    for line in cleaned:
        if prev is not None and line == prev and line.strip():
            continue
        final.append(line)
        prev = line

    return "\n".join(final)


# ---------------------------------------------------------------------------
# Basic extraction
# ---------------------------------------------------------------------------


def extract_text_with_structure(
    pdf_path: str,
    start_page: int | None = None,
    end_page: int | None = None,
    output_file: str | None = None,
    dedup: bool = False,
    x_tol: float = 3.0,
    y_tol: float = 3.0,
) -> str:
    """Extract text from PDF while preserving paragraph and list structure."""
    if start_page is not None:
        start_page -= 1

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        start_page = start_page or 0
        end_page = min(end_page, total_pages) if end_page else total_pages

        print(
            f"Extracting pages {start_page + 1}\u2013{end_page} of {total_pages}..."
        )

        pages_text: List[str] = []
        for idx in range(start_page, end_page):
            page = pdf.pages[idx]
            try:
                text = page.extract_text(
                    x_tolerance=x_tol, y_tolerance=y_tol
                )
            except Exception:
                try:
                    text = page.extract_text()
                except Exception as exc:
                    print(f"Warning: page {idx + 1}: {exc}")
                    text = ""
            pages_text.append(text or "")

    result = "\n\n".join(pages_text)
    result = post_process_text(result)
    if dedup:
        result = dedup_overlapped_text(result)

    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"Saved to {output_file}")

    return result


# ---------------------------------------------------------------------------
# Semantic extraction helpers
# ---------------------------------------------------------------------------


def _collect_lines_for_page(
    page: Any,
    *,
    char_gap_repair: bool,
    x_tol: float,
    y_tol: float,
    line_tol: float,
    gap_scale: float,
) -> Tuple[List[Dict[str, Any]], List[float]]:
    """Extract line dicts and raw font sizes from a single page."""
    if char_gap_repair:
        chars = page.chars
        sizes = [
            c["size"] for c in chars if isinstance(c.get("size"), (int, float))
        ]
        lines = _group_chars_into_lines(
            chars, line_tol=line_tol, gap_scale=gap_scale
        )
    else:
        words = page.extract_words(
            x_tolerance=x_tol,
            y_tolerance=y_tol,
            keep_blank_chars=False,
            use_text_flow=True,
            extra_attrs=["fontname", "size"],
        )
        sizes = [
            w["size"] for w in words if isinstance(w.get("size"), (int, float))
        ]
        lines = _group_words_into_lines(words, line_tol=line_tol)
    return lines, sizes


def _detect_repeating_headers_footers(
    pdf: Any,
    start: int,
    end: int,
    *,
    char_gap_repair: bool,
    x_tol: float,
    y_tol: float,
    line_tol: float,
    gap_scale: float,
) -> Tuple[set, set]:
    """Pre-scan pages to find text that repeats in header/footer bands."""
    header_counter: Counter[str] = Counter()
    footer_counter: Counter[str] = Counter()

    for idx in range(start, end):
        page = pdf.pages[idx]
        page_height = float(page.height or 0)
        header_band = page_height * 0.10
        footer_band = page_height * 0.90
        try:
            lines, _ = _collect_lines_for_page(
                page,
                char_gap_repair=char_gap_repair,
                x_tol=x_tol,
                y_tol=y_tol,
                line_tol=line_tol,
                gap_scale=gap_scale,
            )
        except Exception:
            continue
        for ln in lines:
            t = ln["text"].strip()
            if not t:
                continue
            if ln["top"] <= header_band:
                header_counter[t] += 1
            elif ln["top"] >= footer_band:
                footer_counter[t] += 1

    page_count = max(1, end - start)
    min_freq = max(2, int(0.5 * page_count))
    header_texts = {t for t, c in header_counter.items() if c >= min_freq}
    footer_texts = {t for t, c in footer_counter.items() if c >= min_freq}
    return header_texts, footer_texts


def _render_page_items(
    ordered: List[Tuple[float, Dict[str, Any]]]
) -> str:
    """Render classified page items (lines, tables, images) into Markdown text."""
    page_lines: List[str] = []
    in_code = False

    for _, item in ordered:
        itype = item.get("type")

        if itype == "spacer":
            if in_code:
                page_lines.append("```")
                in_code = False
            page_lines.append("")
            page_lines.append("")
            continue

        if itype == "table":
            if in_code:
                page_lines.append("```")
                in_code = False
            page_lines.append(item["markdown"])
            page_lines.append("")
            continue

        if itype == "image":
            if in_code:
                page_lines.append("```")
                in_code = False
            page_lines.append(item["markdown"])
            continue

        text = item["text"]

        if item.get("is_heading"):
            if in_code:
                page_lines.append("```")
                in_code = False
            level = max(1, min(6, item.get("heading_level", 2)))
            page_lines.append(f"{'#' * level} {text}")
            continue

        if item.get("is_code"):
            if not in_code:
                page_lines.append("```")
                in_code = True
            page_lines.append(text)
            continue

        if in_code:
            page_lines.append("```")
            in_code = False

        if item.get("is_list"):
            m = re.match(
                r"^\s*[\u2022\-\*\u25E6\u25AA\u2013\u2014\u00B7]\s+(.*)", text
            )
            page_lines.append(f"- {m.group(1)}" if m else text)
        else:
            page_lines.append(text)

    if in_code:
        page_lines.append("```")

    return "\n".join(page_lines).rstrip()


# ---------------------------------------------------------------------------
# Semantic extraction (main)
# ---------------------------------------------------------------------------


def extract_text_with_semantics(
    pdf_path: str,
    start_page: int | None = None,
    end_page: int | None = None,
    output_file: str | None = None,
    dedup: bool = False,
    include_images: bool = False,
    embed_tables: bool = False,
    detect_columns: bool = True,
    x_tol: float = 3.0,
    y_tol: float = 3.0,
    line_tol: float = 2.0,
    remove_headers: bool = True,
    char_gap_repair: bool = True,
    gap_scale: float = 1.0,
) -> str:
    """Extract text with semantic structure preservation.

    Detects headings, lists, code blocks, tables, images, and two-column
    layouts to produce clean Markdown-like output.
    """
    if start_page is not None:
        start_page -= 1

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        start_page = start_page or 0
        end_page = min(end_page, total_pages) if end_page else total_pages

        print(
            f"[Semantic] Extracting pages {start_page + 1}\u2013{end_page}"
            f" of {total_pages}..."
        )

        line_opts: Dict[str, Any] = dict(
            char_gap_repair=char_gap_repair,
            x_tol=x_tol,
            y_tol=y_tol,
            line_tol=line_tol,
            gap_scale=gap_scale,
        )

        header_texts: set[str] = set()
        footer_texts: set[str] = set()
        if remove_headers:
            header_texts, footer_texts = _detect_repeating_headers_footers(
                pdf, start_page, end_page, **line_opts
            )

        rendered_pages: List[str] = []

        for page_index in range(start_page, end_page):
            page = pdf.pages[page_index]
            page_width = float(page.width or 0)
            page_height = float(page.height or 0)

            lines, all_sizes = _collect_lines_for_page(page, **line_opts)
            page_median_size = median(all_sizes) if all_sizes else None

            # --- Tables ---
            tables_md: List[Tuple[float, str]] = []
            if embed_tables:
                try:
                    settings = {
                        "vertical_strategy": "lines",
                        "horizontal_strategy": "lines",
                        "snap_tolerance": 3,
                        "join_tolerance": 3,
                    }
                    for t in page.find_tables(table_settings=settings):
                        try:
                            md = _format_markdown_table(t.extract())
                            tables_md.append((float(t.bbox[1]), md))
                        except Exception:
                            continue
                except Exception:
                    pass

            # --- Images ---
            image_placeholders: List[Tuple[float, str]] = []
            if include_images:
                for idx, img in enumerate(page.images):
                    top = float(img.get("top", 0))
                    w = int(img.get("width", 0))
                    h = int(img.get("height", 0))
                    image_placeholders.append(
                        (top, f"[IMAGE p{page_index + 1}-i{idx + 1} {w}x{h}]")
                    )

            # --- Classify text lines ---
            line_items: List[Tuple[float, Dict[str, Any]]] = []
            for ln in lines:
                text = ln["text"].strip()
                if not text:
                    continue

                if remove_headers:
                    if (
                        ln["top"] <= page_height * 0.10
                        and text in header_texts
                    ):
                        continue
                    if (
                        ln["top"] >= page_height * 0.90
                        and text in footer_texts
                    ):
                        continue
                    if ln["top"] <= page_height * 0.15:
                        text = re.sub(r"\s\d{1,4}$", "", text).strip()
                        ln = {**ln, "text": text}

                classified = _classify_line(ln, page_median_size, page_width)
                line_items.append((ln["top"], classified))

            # --- Merge all items ---
            combined: List[Tuple[float, Dict[str, Any]]] = list(line_items)
            combined.extend(
                (top, {"type": "table", "markdown": md, "xmid": page_width * 0.5})
                for top, md in tables_md
            )
            combined.extend(
                (top, {"type": "image", "markdown": ph, "xmid": page_width * 0.5})
                for top, ph in image_placeholders
            )

            # --- Column-aware ordering ---
            if detect_columns and _detect_columns(lines, page_width):
                divider = _compute_column_divider(lines, page_width)
                left = sorted(
                    (
                        c
                        for c in combined
                        if c[1].get("xmid", page_width * 0.5) < divider
                    ),
                    key=lambda t: t[0],
                )
                right = sorted(
                    (
                        c
                        for c in combined
                        if c[1].get("xmid", page_width * 0.5) >= divider
                    ),
                    key=lambda t: t[0],
                )
                ordered = (
                    left
                    + [(float("inf") - 1, {"type": "spacer"})]
                    + right
                )
            else:
                ordered = sorted(combined, key=lambda t: t[0])

            rendered_pages.append(_render_page_items(ordered))

    result = "\n\n".join(rendered_pages)
    result = post_process_text(result)
    if dedup:
        result = dedup_overlapped_text(result)

    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"Saved to {output_file}")

    return result


# ---------------------------------------------------------------------------
# Table extraction
# ---------------------------------------------------------------------------


def extract_tables(
    pdf_path: str,
    start_page: int | None = None,
    end_page: int | None = None,
    output_dir: str | None = None,
) -> List[str]:
    """Extract tables from PDF pages using pdfplumber and save as CSV files."""
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        first = (start_page - 1) if start_page else 0
        last = min(end_page, total_pages) if end_page else total_pages

        if output_dir:
            Path(output_dir).mkdir(parents=True, exist_ok=True)

        saved: List[str] = []
        table_idx = 0

        for page_num in range(first, last):
            page = pdf.pages[page_num]
            for table in page.find_tables():
                rows = table.extract()
                if not rows:
                    continue
                table_idx += 1
                if output_dir:
                    path = str(Path(output_dir) / f"table_{table_idx}.csv")
                    with open(path, "w", newline="", encoding="utf-8") as f:
                        csv.writer(f).writerows(rows)
                    saved.append(path)
                    print(f"  Table {table_idx} -> {path}")

        if table_idx == 0:
            print("No tables found in the specified page range.")
        else:
            print(f"Found {table_idx} table(s).")
        return saved


# ---------------------------------------------------------------------------
# Poppler backend
# ---------------------------------------------------------------------------


def _poppler_extract(
    pdf_path: str,
    start: int | None = None,
    end: int | None = None,
    *,
    dedup: bool = False,
    output_file: str | None = None,
) -> str:
    """Extract text using Poppler's ``pdftotext`` with layout preservation."""
    if shutil.which("pdftotext") is None:
        print(
            "Error: 'pdftotext' not found. Install Poppler utilities "
            "to use --use-poppler.",
            file=sys.stderr,
        )
        sys.exit(2)

    cmd: List[str] = ["pdftotext"]
    if start:
        cmd += ["-f", str(start)]
    if end:
        cmd += ["-l", str(end)]
    cmd += ["-layout", pdf_path, "-"]

    try:
        proc = subprocess.run(cmd, check=True, capture_output=True)
        text = proc.stdout.decode("utf-8", errors="replace")
    except subprocess.CalledProcessError as exc:
        print(f"Poppler extraction failed: {exc}", file=sys.stderr)
        sys.exit(2)

    text = text.replace("\f", "\n")
    text = re.sub(r"[ ]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = post_process_text(text)
    if dedup:
        text = dedup_overlapped_text(text)

    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Saved to {output_file}")

    return text


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _usage_tips() -> str:
    return (
        "\nPDF Extractor \u2014 Usage tips and common examples\n"
        "================================================\n\n"
        "Quick starts\n"
        "  python pdf-extractor.py <file.pdf> --semantic --dedup\n"
        "  python pdf-extractor.py <file.pdf> --semantic --start 5 --end 20 --dedup\n"
        "  python pdf-extractor.py <file.pdf> --semantic -o out.md\n\n"
        "Layout\n"
        "  Disable two-column detection:  --no-column-detect\n"
        "  Keep headers/footers:          --no-header-footer\n"
        "  Disable char-gap repair:       --no-char-gap-repair\n\n"
        "Tables and images\n"
        "  python pdf-extractor.py <file.pdf> --semantic --embed-tables --include-images\n"
        "  python pdf-extractor.py <file.pdf> --extract-tables --tables-dir tables/\n\n"
        "Tuning\n"
        "  --x-tol 2.5 --y-tol 3.5   Adjust word grouping tolerances\n"
        "  --line-tol 2               Adjust line reconstruction tolerance\n"
        "  --gap-scale 0.85           Tighten char-gap spacing\n\n"
        "Alternate backend\n"
        "  python pdf-extractor.py <file.pdf> --use-poppler --dedup\n\n"
        "Full help:  python pdf-extractor.py --help\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract text from PDF with structure preservation",
    )
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument("--start", type=int, help="First page (1-indexed)")
    parser.add_argument("--end", type=int, help="Last page (1-indexed)")
    parser.add_argument("-o", "--output", help="Output file path")
    parser.add_argument(
        "--extract-tables",
        action="store_true",
        help="Extract tables to CSV files (uses pdfplumber)",
    )
    parser.add_argument("--tables-dir", help="Directory for extracted tables")
    parser.add_argument(
        "--dedup",
        action="store_true",
        help="Remove doubled characters (useful for some PDFs)",
    )
    parser.add_argument(
        "--semantic",
        action="store_true",
        help="Semantic extraction: headings, lists, code blocks, optional images/tables",
    )
    parser.add_argument(
        "--include-images",
        action="store_true",
        help="Include image placeholders",
    )
    parser.add_argument(
        "--embed-tables",
        action="store_true",
        help="Embed tables as Markdown",
    )
    parser.add_argument(
        "--no-column-detect",
        action="store_true",
        help="Disable column detection",
    )
    parser.add_argument(
        "--x-tol",
        type=float,
        default=3.0,
        help="X tolerance (default: 3)",
    )
    parser.add_argument(
        "--y-tol",
        type=float,
        default=3.0,
        help="Y tolerance (default: 3)",
    )
    parser.add_argument(
        "--line-tol",
        type=float,
        default=2.0,
        help="Line tolerance (default: 2)",
    )
    parser.add_argument(
        "--no-header-footer",
        action="store_true",
        help="Keep headers/footers",
    )
    parser.add_argument(
        "--no-char-gap-repair",
        action="store_true",
        help="Disable char-gap repair",
    )
    parser.add_argument(
        "--use-poppler",
        action="store_true",
        help="Use Poppler pdftotext backend",
    )
    parser.add_argument(
        "--gap-scale",
        type=float,
        default=1.0,
        help="Char-gap scale (default: 1.0)",
    )
    parser.add_argument(
        "--tips",
        action="store_true",
        help="Show usage tips and exit",
    )

    args = parser.parse_args()

    if args.tips:
        print(_usage_tips())
        return 0

    pdf = Path(args.pdf_path)
    if not pdf.exists():
        print(f"Error: '{args.pdf_path}' not found.", file=sys.stderr)
        return 1

    if args.use_poppler:
        text = _poppler_extract(
            args.pdf_path,
            args.start,
            args.end,
            dedup=args.dedup,
            output_file=args.output,
        )
        print("\nSample of extracted text:")
        print("-" * 40)
        print(text[:500] + "..." if len(text) > 500 else text)
        print("-" * 40)
        return 0

    output_file = args.output or str(pdf.with_suffix(".txt"))

    if args.semantic:
        text = extract_text_with_semantics(
            args.pdf_path,
            start_page=args.start,
            end_page=args.end,
            output_file=output_file,
            dedup=args.dedup,
            include_images=args.include_images,
            embed_tables=args.embed_tables,
            detect_columns=not args.no_column_detect,
            x_tol=args.x_tol,
            y_tol=args.y_tol,
            line_tol=args.line_tol,
            remove_headers=not args.no_header_footer,
            char_gap_repair=not args.no_char_gap_repair,
            gap_scale=args.gap_scale,
        )
    else:
        text = extract_text_with_structure(
            args.pdf_path,
            start_page=args.start,
            end_page=args.end,
            output_file=output_file,
            dedup=args.dedup,
            x_tol=args.x_tol,
            y_tol=args.y_tol,
        )

    if args.extract_tables:
        tables_dir = args.tables_dir or str(pdf.parent / "extracted_tables")
        extract_tables(
            args.pdf_path, args.start, args.end, output_dir=tables_dir
        )

    print("\nSample of extracted text:")
    print("-" * 40)
    print(text[:500] + "..." if len(text) > 500 else text)
    print("-" * 40)
    return 0


if __name__ == "__main__":
    sys.exit(main())
