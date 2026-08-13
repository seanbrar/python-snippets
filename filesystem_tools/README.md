# Filesystem Tools

[![MIT License](https://img.shields.io/badge/license-MIT-green)](../LICENSE)
[![Python 3.x](https://img.shields.io/badge/python-3.x-blue.svg)](https://www.python.org/downloads/)

Utilities for file system inspection and visualization. No external dependencies required.

## Scripts

### ascii_tree.py
Print a directory tree in ASCII format with configurable depth.

**Usage:**
```bash
python filesystem_tools/ascii_tree.py /path/to/directory --depth 3
```

### list_directory.py
Recursively list directory contents with configurable depth and item-count limits.

**Usage:**
```bash
python filesystem_tools/list_directory.py /path/to/directory --max-depth 3 --max-items 10
```

### diagnostic_directory.py
Inspect filenames for Unicode encoding mismatches — curly quotes, invisible characters, and other quirks that cause fuzzy-matching failures.

**Usage:**
```bash
python filesystem_tools/diagnostic_directory.py /path/to/directory
```
