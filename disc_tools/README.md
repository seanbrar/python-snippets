# Disc Image Tools

[![MIT License](https://img.shields.io/badge/license-MIT-green)](../LICENSE)
[![Python 3.x](https://img.shields.io/badge/python-3.x-blue.svg)](https://www.python.org/downloads/)

A collection of scripts for managing disc images (ISO, CHD) and archives.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Scripts](#scripts)
  - [iso_extraction.py](#iso_extractionpy)
  - [iso_cleanup.py](#iso_cleanuppy)
  - [chd_creator.py](#chd_creatorpy)
  - [iso_read.py](#iso_readpy)
- [Common Features](#common-features)
- [Workflow Examples](#workflow-examples)
- [Caution](#caution)

## Prerequisites

- Python 3.x
- `py7zr` library (for ISO extraction)
- `chdman` utility (for CHD conversion, part of MAME tools)

Install Python dependencies:
```bash
pip install py7zr
```

## Scripts

### iso_extraction.py
Extracts ISO files from 7z archives, optimized for slow disk performance.

**Features:**
- Handles single and multi-file archives
- Uses temporary directory for processing
- Supports graceful interruption

**Usage:**
```bash
python iso_extraction.py <folder_path>
```

**Behavior:**
- For single-ISO archives: Extracts directly to source folder
- For multi-file archives: Creates subfolder `extracted_[archive_name]`
- Automatically removes source 7z after successful extraction

### iso_cleanup.py
Removes ISO files that have been successfully converted to CHD format.

**Features:**
- Dry-run mode to preview changes
- Detailed logging of operations
- Space savings calculation

**Usage:**
```bash
python iso_cleanup.py <folder_path>           # Dry run mode
python iso_cleanup.py <folder_path> --execute # Actually delete files
```

### chd_creator.py
Batch converts ISO files to CHD format using MAME's chdman tool.

**Features:**
- Multi-processor support
- Progress tracking
- Skips existing CHD files
- Detailed logging

**Usage:**
```bash
python chd_creator.py <folder_path>
```

**Notes:**
- Uses 16 processors by default for conversion
- Creates log file with timestamp
- Can be safely interrupted with Ctrl+C

### iso_read.py
Analyzes ISO file structure and headers.

**Usage:**
```bash
python iso_read.py <path_to_iso_file>
```

## Common Features

All scripts include:
- Detailed logging to both console and file
- Graceful handling of interruptions
- Progress reporting for long operations

## Examples

**Typical Workflow:**
1. Extract ISOs from archives:
   ```bash
   python iso_extraction.py /path/to/archives
   ```

2. Convert ISOs to CHD:
   ```bash
   python chd_creator.py /path/to/isos
   ```

3. Clean up original ISOs:
   ```bash
   python iso_cleanup.py /path/to/isos --execute
   ```

## Caution

- Always verify CHD files before deleting original ISOs
- Consider backing up important files before batch operations
- Use dry-run options when available to preview changes 