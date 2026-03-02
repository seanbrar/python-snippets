# Python Snippets

[![MIT License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Python 3.x](https://img.shields.io/badge/python-3.x-blue.svg)](https://www.python.org/downloads/)
[![standard-readme compliant](https://img.shields.io/badge/readme%20style-standard-brightgreen.svg?style=flat-square)](https://github.com/RichardLitt/standard-readme)

A collection of Python utility scripts and tools for various tasks including text extraction, file management, transcription, and media organization.

## Table of Contents

- [Background](#background)
- [Install](#install)
- [Usage](#usage)
- [Categories](#categories)
  - [Text Extraction](#text-extraction)
  - [Music Library Tools](#music-library-tools)
  - [File System Tools](#file-system-tools)
  - [ROM Tools](#rom-tools)
  - [Disc Image Tools](#disc-image-tools)
  - [Standalone Utilities](#standalone-utilities)
- [License](#license)

## Background

This repository contains various Python scripts developed for personal use to automate common tasks. Each script is designed to be standalone and focused on a specific utility function. The scripts are organized into thematic categories, with more detailed documentation available in the subdirectory READMEs.

## Install

1. Clone the repository:
   ```bash
   git clone https://github.com/seanbrar/python-snippets.git
   cd python-snippets
   ```

2. Install category-specific dependencies as needed:
   ```bash
   # For music library tools
   pip install -r music_library_tools/requirements.txt

   # For ElevenLabs transcription
   pip install elevenlabs python-dotenv

   # For PDF extraction (optional Poppler backend)
   pip install pdfplumber
   ```

Most scripts require no additional dependencies beyond Python 3.x.

## Usage

Each script can be run independently:

```bash
python script_name.py [OPTIONS] [ARGUMENTS]
```

For detailed usage instructions, refer to the category-specific sections below or the README files in each subdirectory.

## Categories

### Text Extraction

Scripts for extracting and processing text from documents.

- **`pdf-extractor.py`** — Extract text from PDFs with structural analysis, two-column detection, table handling, and optional Poppler backend.
- **`epub_extractor.py`** — Extract chapters from ePub files to plain text, Markdown, or HTML, with optional image extraction.
- **`cite_regex.py`** — Remove citation markers (e.g. `[1]`, `[2]`) from text via regex.
- **`concat_markdown.py`** — Concatenate all `.md` files in a directory into a single file.

### Music Library Tools

Located in `music_library_tools/`. Scripts for organizing and managing a music library.

- **`rename_music_files.py`** — Rename music files by extracting track numbers and applying a disc/track naming convention. Supports `--auto-clean` and `--dry-run`.
- **`music_tree.py`** — Print a directory tree of a music library, optionally writing to file.
- **`music_reorganizer.py`** — Reorganize music files by metadata (artist/album) with issue logging.
- **`metadata_audit.py`** — Audit and correct music file metadata.

Dependencies: see `music_library_tools/requirements.txt`.

[Detailed documentation](./music_library_tools/README.md)

### File System Tools

Utilities for file system inspection and visualization.

- **`ascii_tree.py`** — Print a directory tree in ASCII format with configurable depth.
- **`list_directory.py`** — Recursively list directory contents with depth and item-count limits.
- **`diagnostic_directory.py`** — Inspect filenames for Unicode encoding mismatches (curly quotes, invisible characters, etc.).

### ROM Tools

Located in `rom_tools/`. Scripts for managing ROM file collections.

- **`nes_renamer.py`** — Rename NES ROM files using a DAT XML file.
- **`rom_copy.py`** — Copy and organize ROM files using path mappings and ignore patterns.

[Detailed documentation](./rom_tools/README.md)

### Disc Image Tools

Located in `disc_tools/`. Scripts for disc image management and conversion.

- **`iso_extraction.py`** — Extract ISO files from 7z archives.
- **`chd_creator.py`** — Convert ISO files to CHD format.
- **`iso_cleanup.py`** — Remove ISO files after CHD conversion.
- **`iso_read.py`** — Analyze ISO file headers and structure.
- **`bin_to_chd.py`** — Orchestrate BIN/CUE to CHD conversion pipeline.

Dependencies: `py7zr`, `chdman` (part of MAME tools).

[Detailed documentation](./disc_tools/README.md)

### Standalone Utilities

- **`transcript_elevenlabs.py`** — Transcribe video/audio files using the ElevenLabs API. Requires an `ELEVENLABS_API_KEY` environment variable (or `.env` file).
- **`ups_value.py`** — Evaluate how well a UPS matches a given load (watts, VA, runtime).
- **`base64_convert.py`** — Decode base64 and parse ASN.1 to extract r/s integers (e.g. for ECDSA signatures).
- **`elements-code.py`** — Extract metadata from Elements-style JSON exports.

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
