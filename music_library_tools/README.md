# Python Music Library Tools

[![MIT License](https://img.shields.io/badge/license-MIT-green)](../LICENSE)
[![Python 3.x](https://img.shields.io/badge/python-3.x-blue.svg)](https://www.python.org/downloads/)

## Overview

Python Music Library Tools is a collection of scripts designed to help organize and manage your music library efficiently. These tools perform tasks such as auditing and correcting metadata, reorganizing music files based on metadata, and batch renaming of music files. 

Please note that these scripts were originally developed for personal use and are tailored to specific music library conventions. While efforts have been made to make them more general-purpose, users may need to modify the scripts to fit their particular needs.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
  - [Metadata Audit](#metadata-audit)
  - [Music Reorganizer](#music-reorganizer)
  - [Rename Music Files](#rename-music-files)
- [Contributing](#contributing)
- [License](#license)

## Features

- **Metadata Audit:** Review and correct metadata for your music files, ensuring consistency across albums.
- **Music Reorganizer:** Organize your music library by moving files into structured directories based on metadata.
- **Rename Music Files:** Batch rename music files by adding prefixes or restructuring filenames.

## Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/seanbrar/python-snippets.git
   cd python-snippets/music_library_tools
   ```

2. **Create a Virtual Environment (Optional but Recommended):**

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

## Usage

Ensure you navigate to the `music_library_tools` directory before running the scripts.

### Metadata Audit

**Description:** Audits and corrects metadata for music files within your library.

**Usage:**

```bash
python metadata_audit.py [OPTIONS] LIBRARY_PATH
```

**Options:**

- `--log-file LOG_FILE` : Path to the log file. Default is `metadata_audit_log.json`.
- `--dry-run` : Simulate the actions without making any changes.
- `--categories CATEGORIES [CATEGORIES ...]` : List of allowed album artist categories.

**Example:**

```bash
python metadata_audit.py /path/to/your/music/library --dry-run
```

### Music Reorganizer

**Description:** Reorganizes your music library by structuring directories based on metadata.

**Usage:**

```bash
python music_reorganizer.py [OPTIONS] LIBRARY_PATH
```

**Options:**

- `--log-file LOG_FILE` : Path to the log file. Default is `music_reorg_log.json`.
- `--dry-run` : Simulate the actions without making any changes.

**Example:**

```bash
python music_reorganizer.py /path/to/your/music/library --dry-run
```

### Rename Music Files

**Description:** Batch renames music files according to the convention "disc - track. title". Automatically detects and preserves track numbers from existing filenames. Supports multiple naming patterns and only processes recognized audio formats (.mp3, .flac, .m4a, .opus, .ogg, .wav).

**Usage:**

```bash
python rename_music_files.py [OPTIONS] PATH
```

**Options:**

- `--prefix PREFIX` : Disc number to use in filename (e.g., "1" for "1 - 01. Title"). Default is "1".
- `--dry-run` : Simulate the actions without renaming files.
- `--auto-clean` : Automatically clean filenames by removing special characters and normalizing spacing.

**Examples:**

```bash
# Rename files with disc 1 prefix
python rename_music_files.py "/path/to/music/files" --prefix "1" --dry-run
# Input:  "01 Track Name.flac"
# Output: "1 - 01. Track Name.flac"

# Preview changes with automatic filename cleaning
python rename_music_files.py "/path/to/music/files" --prefix "2" --dry-run --auto-clean
# Input:  "01. Track Name?.flac"
# Output: "2 - 01. Track Name.flac"
```

**Supported Filename Patterns:**
- "01 - Title"
- "01. Title"
- "01 Title"

The script will extract the track number and title from these patterns and reformat them according to the standard convention.

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create a new branch: `git checkout -b feature/YourFeature`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature/YourFeature`
5. Open a pull request.

## License

This project is licensed under the [MIT License](../LICENSE).

## Disclaimer and Cautions

These scripts were developed for personal use and are tailored to specific music library conventions. While efforts have been made to make them more general-purpose, users should be aware of the following:

1. **Potential for Data Loss**: These scripts modify file structures and metadata. Always back up your music library before running these scripts.

2. **Bugs and Limitations**: The scripts may contain bugs or behave unexpectedly with certain file structures or metadata formats. Users should carefully review proposed changes before confirming them.

3. **Manual Intervention**: For optimal results, users should be prepared to manually review and confirm changes, especially for complex or non-standard file structures.

4. **Customization May Be Required**: The scripts may need modification to work with different music library organizations or metadata conventions.

5. **No Warranty**: These scripts are provided "as is", without warranty of any kind. The authors are not responsible for any data loss or other issues that may occur from using these scripts.

6. **Dry Run First**: Always use the `--dry-run` option first to see what changes would be made without actually modifying any files.

7. **Incremental Usage**: Consider running these scripts on small subsets of your library first, rather than your entire collection at once.

Users are encouraged to thoroughly understand the scripts' functionality before use, and to contribute improvements or bug fixes if they encounter issues.