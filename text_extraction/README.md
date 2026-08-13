# Text Extraction

[![MIT License](https://img.shields.io/badge/license-MIT-green)](../LICENSE)
[![Python 3.x](https://img.shields.io/badge/python-3.x-blue.svg)](https://www.python.org/downloads/)

Scripts for extracting and processing text from documents (PDFs, ePubs, Markdown).

## Prerequisites

- Python 3.x
- `pdfplumber` (for PDF extraction)
- `ebooklib`, `beautifulsoup4`, `lxml` (for ePub extraction)

Install dependencies:
```bash
pip install -r requirements.txt
```

Or use the project-level venv (both `pdf_extractor.py` and `epub_extractor.py` auto-detect it):
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r text_extraction/requirements.txt
```

## Scripts

### pdf_extractor.py
Extract text from PDFs with structural analysis, two-column detection, table handling, and optional Poppler backend.

**Usage:**
```bash
python text_extraction/pdf_extractor.py document.pdf --semantic --dedup
python text_extraction/pdf_extractor.py document.pdf --semantic --start 5 --end 20 -o out.md
python text_extraction/pdf_extractor.py document.pdf --extract-tables --tables-dir tables/
```

Run `python text_extraction/pdf_extractor.py --tips` for more examples.

### epub_extractor.py
Extract chapters from ePub files to plain text, Markdown, or HTML. Supports image extraction and combined multi-chapter output.

**Usage:**
```bash
python text_extraction/epub_extractor.py book.epub --chapters 1 2 3
python text_extraction/epub_extractor.py book.epub --chapters 7 8 --output-format markdown
python text_extraction/epub_extractor.py book.epub --chapters 1 2 3 --combined-markdown out.md
```

### cite_regex.py
Remove citation markers (e.g. `[1]`, `[2]`) from text via regex.

**Usage:**
```bash
python text_extraction/cite_regex.py
```

### concat_markdown.py
Concatenate all `.md` files in a directory into a single output file.

**Usage:**
```bash
python text_extraction/concat_markdown.py <input_directory> <output_file>
```
