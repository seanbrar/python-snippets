# ROM Tools

[![MIT License](https://img.shields.io/badge/license-MIT-green)](../LICENSE)
[![Python 3.x](https://img.shields.io/badge/python-3.x-blue.svg)](https://www.python.org/downloads/)

Scripts for managing and organizing ROM file collections.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Scripts](#scripts)
  - [nes_renamer.py](#nes_renamerpy)
  - [rom_copy.py](#rom_copypy)
- [Best Practices](#best-practices)
- [Examples](#examples)
- [Caution](#caution)

## Prerequisites
- Python 3.x
- No additional libraries required

## Scripts

### nes_renamer.py
Renames NES ROM files to match standard naming conventions.

**Features:**
- Supports No-Intro DAT format
- Handles multiple regions
- Preserves original files by default

**Usage:**
```bash
python nes_renamer.py <input_directory> <dat_file_path>
```

**Example Output:**
```
Processing: Super Mario Bros. (Japan, USA).nes
  Renamed to: Super Mario Bros. (Japan, USA) [!].nes
Processing: Contra (USA).nes
  Renamed to: Contra (USA) [!].nes
```

### rom_copy.py
Organizes ROM files according to predefined rules.

**Features:**
- File integrity verification
- Structured directory creation
- Detailed operation logging

**Usage:**
```bash
python rom_copy.py [OPTIONS] SOURCE_DIR DEST_DIR
```

**Options:**
- `--verify`: Perform checksum verification
- `--log-file PATH`: Specify custom log file path
- `--dry-run`: Preview changes without copying files

## Best Practices
- Always verify ROM collections after operations
- Keep original files until verification is complete
- Use consistent naming conventions across collections

## Examples

**Standardize NES ROM Names:**
```bash
python nes_renamer.py ./my_roms ./database.dat
```

**Organize ROM Collection:**
```bash
python rom_copy.py ./unsorted_roms ./organized_collection
```

## Caution
- These scripts modify file names and locations
- Always back up your ROM collection before running these scripts
- Use the dry-run options when available to preview changes
