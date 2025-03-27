# Python Snippets

[![GitHub License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Python 3.x](https://img.shields.io/badge/python-3.x-blue.svg)](https://www.python.org/downloads/)
[![standard-readme compliant](https://img.shields.io/badge/readme%20style-standard-brightgreen.svg?style=flat-square)](https://github.com/RichardLitt/standard-readme)

A collection of standalone Python utility scripts for file management, media organization, and system tasks.

## Table of Contents

- [Background](#background)
- [Install](#install)
- [Usage](#usage)
- [Categories](#categories)
  - [Music Library Tools](#music-library-tools)
  - [File System Tools](#file-system-tools)
  - [ROM Tools](#rom-tools)
  - [Disc Image Tools](#disc-image-tools)
- [Contributing](#contributing)
- [License](#license)

## Background

This repository contains various Python scripts I've developed for personal use to automate common tasks. Each script is designed to be standalone and focused on a specific utility function. While originally created for personal use, these scripts have been refined to be more accessible and useful for others.

The scripts are organized into thematic categories, with more detailed documentation available in the subdirectory READMEs.

## Install

1. Clone the repository:
   ```bash
   git clone https://github.com/seanbrar/python-snippets.git
   ```

2. Navigate to the project directory:
   ```bash
   cd python-snippets
   ```

3. Install category-specific dependencies as needed:
   ```bash
   # For music library tools
   cd music_library_tools
   pip install -r requirements.txt
   ```

Most scripts require no additional dependencies beyond Python 3.x. Specific requirements are noted in each category section below.

## Usage

Each script can be run independently using Python:

```bash
python script_name.py [OPTIONS] [ARGUMENTS]
```

For detailed usage instructions, refer to the category-specific sections below or the README files in each subdirectory.

## Categories

### Music Library Tools

Located in the `music_library_tools` folder, these scripts help organize and manage a music library.

**Key Scripts:**
- `metadata_audit.py`: Audits and corrects metadata for music files
- `music_reorganizer.py`: Reorganizes music files based on metadata
- `rename_music_files.py`: Batch renames music files in a specified directory

**Dependencies:**
- See `music_library_tools/requirements.txt`

[Detailed documentation](./music_library_tools/README.md)

### File System Tools

Utilities for file system management and visualization.

**Key Scripts:**
- `ascii_tree.py`: Prints a directory tree structure in ASCII format

**Usage Example:**
```bash
python ascii_tree.py /home/user/documents -d 3 -f
```

### ROM Tools

Located in the `rom_tools` folder, these scripts help manage ROM file collections.

**Key Scripts:**
- `nes_renamer.py`: Renames NES ROM files based on a provided DAT file
- `rom_copy.py`: Manages ROM file organization and verification

**Dependencies:**
- No additional dependencies required

[Detailed documentation](./rom_tools/README.md)

### Disc Image Tools

Located in the `disc_tools` folder, these scripts handle disc image management and conversion.

**Key Scripts:**
- `iso_extraction.py`: Extracts ISO files from 7z archives
- `chd_creator.py`: Converts ISO files to CHD format
- `iso_cleanup.py`: Manages ISO files after CHD conversion
- `iso_read.py`: Analyzes ISO file headers and structure

**Dependencies:**
- `py7zr` library (for ISO extraction)
- `chdman` utility (for CHD conversion, part of MAME tools)

[Detailed documentation](./disc_tools/README.md)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
