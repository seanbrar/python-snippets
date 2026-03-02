#!/usr/bin/env python3
"""
Epub Chapter Extractor

Extracts specific chapters from an ePub file, with output as plain text,
Markdown, or HTML.  Supports image extraction and combined multi-chapter output.

Use the project venv from the repo root:  .venv/bin/python epub_extractor.py ...
Or activate first:  source .venv/bin/activate

Usage:
    .venv/bin/python epub_extractor.py book.epub --chapters 1 2 3
    python epub_extractor.py book.epub --chapters 7 8 --output-format markdown
    python epub_extractor.py book.epub --chapters 1 2 3 --combined-markdown out.md
    python epub_extractor.py book.epub --chapters 5 --save-images --image-naming by-figure
"""

import os
import sys

if __name__ == "__main__":
    _script_dir = os.path.dirname(os.path.abspath(__file__))
    _venv_python = os.path.join(_script_dir, ".venv", "bin", "python")
    if os.path.exists(_venv_python) and os.path.realpath(
        sys.executable
    ) != os.path.realpath(_venv_python):
        os.execv(_venv_python, [_venv_python] + sys.argv)

import argparse
import posixpath
import re
import tempfile
import zipfile
from typing import Any, Dict, List, Optional, Tuple

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup, NavigableString, Tag

try:
    from markdownify import markdownify as html_to_md
except Exception:  # pragma: no cover - optional
    html_to_md = None


def _open_epub_robust(epub_path: str) -> Tuple[Any, Optional[str]]:
    """Open an EPUB file; on 'missing item' errors, try a copy with URL manifest entries removed.

    Returns (book, temp_path). If temp_path is set, the caller should os.unlink(temp_path) when done.
    """
    try:
        book = epub.read_epub(epub_path)
        return book, None
    except Exception as exc:
        err_msg = str(exc).lower()
        if "no item named" not in err_msg and "there is no item" not in err_msg:
            raise

    # Build a sanitized copy: remove manifest items whose href is an external URL.
    with zipfile.ZipFile(epub_path, "r") as zf:
        try:
            container = zf.read("META-INF/container.xml").decode("utf-8", errors="replace")
        except KeyError:
            raise RuntimeError("EPUB has no META-INF/container.xml") from exc

        # Get OPF path from container (first rootfile).
        opf_match = re.search(r'<rootfile[^>]+full-path="([^"]+)"', container)
        if not opf_match:
            raise RuntimeError("Could not find OPF path in container.xml") from exc
        opf_path = opf_match.group(1).strip()

        opf_dir = posixpath.dirname(opf_path)
        opf_bytes = zf.read(opf_path)
        opf_text = opf_bytes.decode("utf-8", errors="replace")

        try:
            soup = BeautifulSoup(opf_text, "xml")
        except Exception:
            import warnings
            from bs4 import XMLParsedAsHTMLWarning
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", XMLParsedAsHTMLWarning)
                soup = BeautifulSoup(opf_text, "html.parser")
        manifest = soup.find("manifest")
        if not manifest:
            raise RuntimeError("No manifest in OPF") from exc

        removed_ids: set = set()
        for item in list(manifest.find_all("item")):
            href = (item.get("href") or "").strip()
            if href.lower().startswith("http://") or href.lower().startswith("https://"):
                removed_ids.add(item.get("id") or "")
                item.decompose()

        for itemref in list(soup.find_all("itemref")):
            if itemref.get("idref") in removed_ids:
                itemref.decompose()

        new_opf = soup.encode("utf-8")

        fd, temp_path = tempfile.mkstemp(suffix=".epub")
        try:
            with os.fdopen(fd, "wb") as out:
                with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
                    for name in zf.namelist():
                        if name == opf_path:
                            zout.writestr(name, new_opf)
                        else:
                            zout.writestr(name, zf.read(name))
        except Exception:
            os.unlink(temp_path)
            raise

    book = epub.read_epub(temp_path)
    return book, temp_path


# ---------------------------------------------------------------------------
# HTML conversion
# ---------------------------------------------------------------------------


def extract_text_from_html(html_content: str) -> str:
    """Extract clean plain text from HTML, preserving paragraph structure."""
    soup = BeautifulSoup(html_content, "html.parser")

    for tag in soup(["script", "style"]):
        tag.decompose()

    for br in soup.find_all("br"):
        br.replace_with("\n")

    parts: List[str] = []
    for block in soup.find_all(
        ["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "pre", "code"]
    ):
        content = block.get_text(" ", strip=True)
        if content:
            parts.append(content)
            if block.name in {"p", "li", "pre"}:
                parts.append("")

    text = "\n".join(parts)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Remove stray XML/HTML processing instruction fragments
    text = re.sub(r"\n*xml\s+version=[^\n]*\n*", "\n", text, flags=re.IGNORECASE)
    return text.strip()


def _inline_to_markdown(elem: Tag) -> str:
    """Recursively render inline children of a block element as Markdown.

    Unlike a flat ``find_all``, this walks the tree depth-first so that
    ``<p>Hello <strong>bold <em>and italic</em></strong></p>``
    correctly produces ``Hello **bold *and italic***`` instead of
    duplicating text for every nested element.
    """
    parts: List[str] = []
    for child in elem.children:
        if isinstance(child, NavigableString):
            parts.append(str(child))
        elif isinstance(child, Tag):
            name = child.name
            inner = _inline_to_markdown(child)
            if name in {"strong", "b"}:
                s = inner.strip()
                parts.append(f"**{s}**" if s else "")
            elif name in {"em", "i"}:
                s = inner.strip()
                parts.append(f"*{s}*" if s else "")
            elif name == "code":
                s = inner.strip()
                parts.append(f"`{s}`" if s else "")
            elif name == "a":
                href = child.get("href", "")
                parts.append(f"[{inner.strip()}]({href})")
            elif name == "img":
                parts.append(f"![{child.get('alt', '')}]({child.get('src', '')})")
            elif name == "br":
                parts.append("\n")
            else:
                parts.append(inner)
    return "".join(parts) or elem.get_text()


def convert_html_to_markdown(html_content: str) -> str:
    """Convert HTML to Markdown.

    Uses *markdownify* when available.  Otherwise falls back to a
    block-level structural converter that handles inline formatting
    recursively (avoiding the duplicate-text bug of flat ``find_all``).
    """
    if html_to_md is not None:
        try:
            return html_to_md(html_content, heading_style="ATX")
        except Exception:
            pass

    soup = BeautifulSoup(html_content, "html.parser")
    parts: List[str] = []

    for elem in soup.find_all(
        ["h1", "h2", "h3", "h4", "h5", "h6", "p", "pre", "li", "img"]
    ):
        name = elem.name
        if name and name[0] == "h" and len(name) == 2 and name[1].isdigit():
            level = int(name[1])
            parts.append("#" * level + " " + _inline_to_markdown(elem).strip())
            parts.append("")
        elif name == "p":
            text = _inline_to_markdown(elem).strip()
            if text:
                parts.append(text)
                parts.append("")
        elif name == "pre":
            parts.append("```\n" + elem.get_text() + "\n```")
            parts.append("")
        elif name == "li":
            parts.append("- " + _inline_to_markdown(elem).strip())
        elif name == "img":
            parts.append(f"![{elem.get('alt', '')}]({elem.get('src', '')})")

    out = "\n".join(parts)
    out = re.sub(r"\n{3,}", "\n\n", out)
    out = re.sub(r"\n*xml\s+version=[^\n]*\n*", "\n", out, flags=re.IGNORECASE)
    return out.strip()


# ---------------------------------------------------------------------------
# Chapter discovery
# ---------------------------------------------------------------------------

# Require chapter number at start of title or after "chapter"/"ch"/space.
# Exclude "G.1" (use (?:^|\s) so "." before digit doesn't count) and exclude
# "1.1", "1.2" (use (?![0-9]) so section numbers don't overwrite chapter 1).
_CHAPTER_RE = re.compile(
    r"chapter\s*(\d+)|\bch\s*(\d+)\b|(?:^|\s)(\d+)(?:\s*[-.:]\s*(?![0-9])|\s+)",
    re.IGNORECASE,
)
_FILENAME_CHAPTER_RE = re.compile(
    r"ch(?:ap(?:ter)?)?[_-]?(\d+)|(\d+)[_-]?ch(?:ap(?:ter)?)?|chapter(\d+)",
    re.IGNORECASE,
)
# Same exclusions as _CHAPTER_RE: no "1.1" section numbers as chapter 1
_HEADING_CHAPTER_RE = re.compile(
    r"chapter\s+(\d+)|\bch\s*(\d+)\b|^(\d+)(?:[.:]\s*(?![0-9])|\s)", re.IGNORECASE
)
# Filename like ch01_pg0001.xhtml or ch14_pg0002.xhtml -> chapter number
_CH_FILENAME_NUM_RE = re.compile(r"ch(\d+)_", re.IGNORECASE)


def _chapter_num_from_title(title: str) -> Optional[int]:
    """Extract a chapter number from a title string, or return ``None``."""
    m = _CHAPTER_RE.search(title)
    if m:
        return int(m.group(1) or m.group(2) or m.group(3))
    return None


def _register_chapter(
    chapters: Dict[int, Dict[str, str]],
    title: str,
    *,
    href: Optional[str] = None,
    item: Optional[Any] = None,
) -> None:
    """Register a chapter if a number can be parsed from *title*."""
    num = _chapter_num_from_title(title)
    if num is None:
        return
    info: Dict[str, str] = {"title": title}
    if href:
        info["href"] = href.split("#")[0]
    if item is not None:
        info["item_id"] = item.get_id()
        info["filename"] = item.get_name()
    chapters[num] = info


def _get_chapter_document_items(
    book: epub.EpubBook, chapter_num: int
) -> List[Dict[str, str]]:
    """Return all document items belonging to a chapter, sorted by filename.

    Matches filenames like ch01_pg0001.xhtml, ch02_pg0003.xhtml (ch<num>_).
    """
    out: List[Dict[str, str]] = []
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        name = item.get_name()
        m = _CH_FILENAME_NUM_RE.search(name)
        if m and int(m.group(1)) == chapter_num:
            out.append({
                "item_id": item.get_id(),
                "filename": name,
                "href": name,
            })
    out.sort(key=lambda x: x["filename"])
    return out


def _resolve_toc_link(
    book: epub.EpubBook,
    title: str,
    href: Optional[str],
    chapters: Dict[int, Dict[str, str]],
    *,
    verbose: bool = True,
) -> None:
    """Resolve a TOC entry's href to a book item and register the chapter.

    Extracted to avoid repeating the href→item lookup three times inside the
    recursive TOC walker.
    """
    if verbose:
        if href:
            print(f"  {title} -> {href}")
        else:
            print(f"  {title}")
    base_href = href.split("#")[0] if href else None
    item = None
    if base_href:
        try:
            item = book.get_item_with_href(base_href)
        except Exception:
            pass
    _register_chapter(chapters, title, href=href, item=item)


def find_chapters_in_toc(
    book: epub.EpubBook, *, verbose: bool = True
) -> Dict[int, Dict[str, str]]:
    """Find chapter information from the table of contents."""
    chapters: Dict[int, Dict[str, str]] = {}
    try:
        toc = book.toc
    except Exception as exc:
        print(f"Could not read table of contents: {exc}")
        return chapters

    if not toc:
        return chapters

    if verbose:
        print("Found table of contents entries:")

    def walk(entries: list) -> None:
        for entry in entries:
            if isinstance(entry, epub.Link):
                _resolve_toc_link(
                    book, entry.title, entry.href, chapters, verbose=verbose
                )
            elif isinstance(entry, tuple) and entry:
                first, rest = entry[0], entry[1] if len(entry) > 1 else []
                if isinstance(first, epub.Link):
                    _resolve_toc_link(
                        book, first.title, first.href, chapters, verbose=verbose
                    )
                else:
                    title = getattr(first, "title", None)
                    if title:
                        if verbose:
                            print(f"  Section: {title}")
                        _register_chapter(chapters, title)
                if isinstance(rest, (list, tuple)):
                    walk(rest)
            else:
                title = getattr(entry, "title", None)
                href = getattr(entry, "href", None)
                if title:
                    _resolve_toc_link(
                        book, title, href, chapters, verbose=verbose
                    )

    walk(toc)
    return chapters


def find_chapters_by_filename(
    book: epub.EpubBook, *, verbose: bool = True
) -> Dict[int, Dict[str, Any]]:
    """Find chapters by filename; each chapter gets all matching documents in order."""
    chapters: Dict[int, Dict[str, Any]] = {}
    if verbose:
        print("Analyzing document files for chapter patterns:")
    try:
        seen_nums: set = set()
        for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            filename = item.get_name()
            if verbose:
                print(f"  {filename}")
            m = _FILENAME_CHAPTER_RE.search(filename)
            if m:
                num = int(m.group(1) or m.group(2) or m.group(3))
                if num not in seen_nums:
                    seen_nums.add(num)
                    items = _get_chapter_document_items(book, num)
                    if items:
                        chapters[num] = {
                            "title": f"Chapter {num}",
                            "items": items,
                        }
    except Exception as exc:
        print(f"Error scanning document items: {exc}")
    return chapters


def find_chapters_by_content(
    book: epub.EpubBook, *, verbose: bool = True
) -> Dict[int, Dict[str, Any]]:
    """Find chapters by headings; each chapter gets all matching documents in order."""
    chapters: Dict[int, Dict[str, Any]] = {}
    if verbose:
        print("Searching document content for chapter headings:")
    for item in book.get_items():
        if item.get_type() != ebooklib.ITEM_DOCUMENT:
            continue
        try:
            content = item.get_content().decode("utf-8", errors="ignore")
            soup = BeautifulSoup(content, "html.parser")
            for heading in soup.find_all(["h1", "h2", "h3", "h4"]):
                heading_text = heading.get_text().strip()
                m = _HEADING_CHAPTER_RE.search(heading_text)
                if m:
                    num = int(m.group(1) or m.group(2) or m.group(3))
                    if num not in chapters:
                        items = _get_chapter_document_items(book, num)
                        if items:
                            chapters[num] = {
                                "title": heading_text,
                                "items": items,
                            }
                            if verbose:
                                print(f"  Found: {heading_text} in {item.get_name()}")
        except Exception as exc:
            print(f"Error processing {item.get_name()}: {exc}")

    return chapters


# ---------------------------------------------------------------------------
# Image / href helpers
# ---------------------------------------------------------------------------


def _resolve_href_relative(item_name: str, href: str) -> Optional[str]:
    """Resolve a relative href against the item's directory path."""
    if not href or href.startswith("#") or re.match(r"^https?://", href):
        return None
    base_dir = posixpath.dirname(item_name)
    return posixpath.normpath(posixpath.join(base_dir, href))


def _extract_figure_number(img_tag: Tag) -> Optional[str]:
    """Try to detect a figure number from a nearby ``<figcaption>`` or alt text."""
    parent = img_tag.find_parent("figure")
    caption_text = None
    if parent:
        cap = parent.find("figcaption")
        if cap:
            caption_text = cap.get_text(" ", strip=True)
    if not caption_text:
        caption_text = img_tag.get("alt", "")
    if caption_text:
        m = re.search(r"fig(?:ure)?\s*(\d+)", caption_text, re.IGNORECASE)
        if m:
            return m.group(1)
    return None


# ---------------------------------------------------------------------------
# Content extraction
# ---------------------------------------------------------------------------


def _fetch_chapter_html(
    book: epub.EpubBook, chapter_info: Dict[str, str]
) -> Tuple[Optional[str], Optional[Any]]:
    """Try to retrieve HTML content for a chapter via item_id, href, or filename."""
    if "item_id" in chapter_info:
        try:
            item = book.get_item_with_id(chapter_info["item_id"])
            if item:
                return item.get_content().decode("utf-8", errors="ignore"), item
        except Exception:
            pass

    if "href" in chapter_info:
        base_href = chapter_info["href"].split("#")[0]
        try:
            item = book.get_item_with_href(base_href)
            if item:
                return item.get_content().decode("utf-8", errors="ignore"), item
        except Exception:
            pass

    if "filename" in chapter_info:
        target = chapter_info["filename"]
        for item in book.get_items():
            if item.get_name() == target:
                try:
                    return item.get_content().decode("utf-8", errors="ignore"), item
                except Exception:
                    break

    return None, None


def _save_chapter_images(
    book: epub.EpubBook,
    soup: BeautifulSoup,
    item: Any,
    chapter_output_dir: str,
    image_naming: str = "by-index",
) -> Dict[str, str]:
    """Extract and save images referenced in *soup*.

    Returns ``{original_href: saved_relpath}``.
    """
    images_dir = os.path.join(chapter_output_dir, "images")
    os.makedirs(images_dir, exist_ok=True)
    mapping: Dict[str, str] = {}
    index = 1

    for img in soup.find_all("img"):
        src = img.get("src")
        resolved = _resolve_href_relative(item.get_name() if item else "", src or "")
        if not resolved:
            continue
        try:
            img_item = book.get_item_with_href(resolved)
        except Exception:
            continue
        if not img_item:
            continue

        ext = os.path.splitext(img_item.get_name())[-1] or ".img"
        filename = None
        if image_naming == "by-figure":
            fig_no = _extract_figure_number(img)
            if fig_no:
                filename = f"figure_{fig_no}{ext}"
        if not filename:
            filename = f"image_{index:03d}{ext}"
        index += 1

        dest = os.path.join(images_dir, filename)
        dedup = 1
        while os.path.exists(dest):
            stem = os.path.splitext(filename)[0]
            dest = os.path.join(images_dir, f"{stem}_{dedup}{ext}")
            dedup += 1

        try:
            with open(dest, "wb") as f:
                f.write(img_item.get_content())
        except Exception as exc:
            print(f"Error saving image {resolved}: {exc}")
            continue

        rel_path = os.path.relpath(dest, chapter_output_dir)
        img["src"] = rel_path
        mapping[resolved] = rel_path

    return mapping


def _render_one_document(
    book: epub.EpubBook,
    doc_info: Dict[str, str],
    output_format: str,
    save_images: bool,
    image_naming: str,
    chapter_output_dir: Optional[str],
) -> Tuple[str, Dict[str, str]]:
    """Fetch one document and return (rendered_content, img_map)."""
    html_content, item = _fetch_chapter_html(book, doc_info)
    if html_content is None:
        return "", {}

    soup = BeautifulSoup(html_content, "html.parser")
    img_map: Dict[str, str] = {}
    if save_images and chapter_output_dir:
        img_map = _save_chapter_images(
            book, soup, item, chapter_output_dir, image_naming
        )

    if output_format == "html":
        body = soup.body or soup
        rendered = str(body)
    elif output_format == "markdown":
        rendered = convert_html_to_markdown(str(soup))
    else:
        rendered = extract_text_from_html(str(soup))

    rendered = re.sub(
        r"\n*(?:<\?)?xml\s+version=[^\n>]*\??(?:\?>)?\s*\n*",
        "\n",
        rendered,
        flags=re.IGNORECASE,
    )
    return rendered, img_map


def extract_chapter_content(
    book: epub.EpubBook,
    chapter_info: Dict[str, Any],
    *,
    output_format: str = "text",
    save_images: bool = False,
    image_naming: str = "by-index",
    chapter_num: Optional[int] = None,
    chapter_output_dir: Optional[str] = None,
) -> Tuple[str, Dict[str, str]]:
    """Extract chapter content (one or many documents) in the requested format.

    When chapter_info has "items", concatenates all documents in order.
    Returns ``(rendered_text, {original_image_href: saved_relpath})``.
    """
    items_list: List[Dict[str, str]] = chapter_info.get("items")
    if not items_list:
        items_list = [chapter_info]  # type: ignore[list-item]

    parts: List[str] = []
    combined_img_map: Dict[str, str] = {}

    for doc_info in items_list:
        rendered, img_map = _render_one_document(
            book,
            doc_info,
            output_format,
            save_images,
            image_naming,
            chapter_output_dir,
        )
        if rendered:
            parts.append(rendered)
        combined_img_map.update(img_map)

    return "\n\n".join(parts), combined_img_map


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------


def _discover_chapters(
    book: epub.EpubBook, *, verbose: bool = True
) -> Dict[int, Dict[str, str]]:
    """Run all three discovery methods and merge (TOC results take priority)."""
    if verbose:
        print("\n" + "=" * 50)
        print("METHOD 1: Searching Table of Contents")
        print("=" * 50)
    toc = find_chapters_in_toc(book, verbose=verbose)

    if verbose:
        print("\n" + "=" * 50)
        print("METHOD 2: Analyzing Filenames")
        print("=" * 50)
    by_filename = find_chapters_by_filename(book, verbose=verbose)

    if verbose:
        print("\n" + "=" * 50)
        print("METHOD 3: Searching Content")
        print("=" * 50)
    by_content = find_chapters_by_content(book, verbose=verbose)

    merged: Dict[int, Dict[str, Any]] = {}
    merged.update(by_filename)
    merged.update(by_content)
    # Only let TOC overwrite when it has a real link and we don't already have
    # a full chapter (multiple "items"). Section headers with no link must not
    # overwrite; TOC single-item must not overwrite when we have full chapter.
    for num, info in toc.items():
        has_link = info.get("href") or info.get("item_id") or info.get("filename")
        existing = merged.get(num)
        if has_link and (existing is None or "items" not in existing):
            merged[num] = info
        elif num not in merged:
            merged[num] = info
    return merged


def _write_individual_chapter(
    content: str,
    chapter_info: Dict[str, str],
    chapter_num: int,
    chapter_dir: str,
    output_format: str,
    img_map: Dict[str, str],
    save_images: bool,
) -> None:
    """Write a single chapter to its own file."""
    ext = {"text": "txt", "markdown": "md", "html": "html"}[output_format]
    output_file = os.path.join(chapter_dir, f"chapter_{chapter_num}.{ext}")
    title = chapter_info["title"]

    with open(output_file, "w", encoding="utf-8") as f:
        if output_format == "html":
            f.write(f"<!-- CHAPTER {chapter_num}: {title} -->\n")
        else:
            f.write(f"CHAPTER {chapter_num}: {title}\n")
            f.write("=" * 60 + "\n\n")
        f.write(content)

    print(f"  Saved to: {output_file}")
    if save_images and img_map:
        print(
            f"  Saved {len(img_map)} image(s) under "
            f"{os.path.join(chapter_dir, 'images')}"
        )
    print(f"  Content length: {len(content):,} characters")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract specific chapters from an ePub file",
    )
    parser.add_argument("epub_file", help="Path to the ePub file")
    parser.add_argument(
        "--chapters",
        nargs="+",
        type=int,
        default=[7, 8],
        help="Chapter numbers to extract (default: 7 8)",
    )
    parser.add_argument(
        "--output-dir",
        default="extracted_chapters",
        help="Output directory for extracted chapters",
    )
    parser.add_argument(
        "--output-format",
        choices=["text", "markdown", "html"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--save-images",
        action="store_true",
        help="Save images referenced by chapters into an images/ subfolder",
    )
    parser.add_argument(
        "--image-naming",
        choices=["by-index", "by-figure"],
        default="by-index",
        help="Image file naming strategy (default: by-index)",
    )
    parser.add_argument(
        "--combined-markdown",
        help="Save all selected chapters into a single Markdown file",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress discovery diagnostics",
    )

    args = parser.parse_args()

    if not os.path.exists(args.epub_file):
        print(f"Error: File '{args.epub_file}' not found.", file=sys.stderr)
        return 1

    os.makedirs(args.output_dir, exist_ok=True)

    combined_mode = bool(args.combined_markdown)
    combined_sections: List[str] = []
    combined_dir: Optional[str] = None
    if combined_mode:
        if args.output_format != "markdown":
            print("Note: Forcing output format to 'markdown' for combined output.")
            args.output_format = "markdown"
        combined_dir = os.path.dirname(args.combined_markdown) or "."
        os.makedirs(combined_dir, exist_ok=True)

    verbose = not args.quiet

    temp_epub_path: Optional[str] = None
    try:
        if verbose:
            print(f"Opening ePub file: {args.epub_file}")
        book, temp_epub_path = _open_epub_robust(args.epub_file)
    except Exception as exc:
        print(f"Error: Could not open ePub file: {exc}", file=sys.stderr)
        return 1

    try:
        all_chapters = _discover_chapters(book, verbose=verbose)

        if verbose:
            print(f"\n{'=' * 50}")
            print("SUMMARY: Found chapters")
            print("=" * 50)
            for num in sorted(all_chapters):
                print(f"  Chapter {num}: {all_chapters[num]['title']}")

        print(f"\n{'=' * 50}")
        print(f"EXTRACTING CHAPTERS: {args.chapters}")
        print("=" * 50)

        extracted = 0
        for chapter_num in args.chapters:
            if chapter_num not in all_chapters:
                print(f"\n  Chapter {chapter_num} not found in the book")
                continue

            print(f"\nExtracting Chapter {chapter_num}...")
            chapter_info = all_chapters[chapter_num]

            chapter_dir = args.output_dir
            if args.save_images or args.output_format in {"html", "markdown"}:
                if combined_mode:
                    chapter_dir = combined_dir
                else:
                    chapter_dir = os.path.join(args.output_dir, f"chapter_{chapter_num}")
                    os.makedirs(chapter_dir, exist_ok=True)

            content, img_map = extract_chapter_content(
                book,
                chapter_info,
                output_format=args.output_format,
                save_images=args.save_images,
                image_naming=args.image_naming,
                chapter_num=chapter_num,
                chapter_output_dir=chapter_dir,
            )

            if not content.strip():
                print(f"  No content found for Chapter {chapter_num}")
                continue

            extracted += 1

            if combined_mode:
                header = f"## Chapter {chapter_num}: {chapter_info['title']}"
                combined_sections.append(f"{header}\n\n{content.strip()}")
                if args.save_images and img_map:
                    print(f"  Saved {len(img_map)} image(s)")
                print("  Appended to combined output")
            else:
                _write_individual_chapter(
                    content,
                    chapter_info,
                    chapter_num,
                    chapter_dir,
                    args.output_format,
                    img_map,
                    args.save_images,
                )

        if combined_mode and combined_sections:
            with open(args.combined_markdown, "w", encoding="utf-8") as f:
                f.write("\n\n".join(combined_sections).rstrip() + "\n")
            print(f"\nCombined Markdown saved to: {args.combined_markdown}")

        print(
            f"\nExtraction complete — {extracted}/{len(args.chapters)} chapter(s) extracted."
        )
        if args.output_format == "markdown" and html_to_md is None:
            print(
                "Tip: Install markdownify for better Markdown:  pip install markdownify"
            )

        return 0 if extracted > 0 else 1
    finally:
        if temp_epub_path:
            try:
                os.unlink(temp_epub_path)
            except OSError:
                pass


if __name__ == "__main__":
    sys.exit(main())
