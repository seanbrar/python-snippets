# Python Snippets

This repository contains a collection of disconnected Python scripts for various purposes. Each script is standalone and can be run independently.

## Getting Started

### Prerequisites

- Python 3.x

### Dependencies

Some scripts require additional Python libraries. These are listed in the `requirements.txt` file in the `music_library_tools` folder.

Install the dependencies using:

```bash
cd music_library_tools
pip install -r requirements.txt
```

Most scripts require no additional dependencies. Exceptions are noted in the script descriptions.

### Usage

1. Clone the repository:
   ```
   git clone https://github.com/seanbrar/python-snippets.git
   ```

2. Navigate to the project directory:
   ```
   cd python-snippets
   ```

3. Run any script using Python:
   ```
   python script_name.py
   ```

## Script Categories

### Music Library Tools

Located in the `music_library_tools` folder, these scripts help organize and manage a music library:

1. `music_reorganizer.py`: Reorganizes music files based on metadata.
   - Cleans album names and sanitizes filenames
   - Moves files to structured directories based on metadata
   - Usage: `python music_reorganizer.py [OPTIONS] LIBRARY_PATH`

2. `rename_music_files.py`: Batch renames music files in a specified directory.
   - Adds a customizable prefix to filenames
   - Provides a dry-run option for previewing changes
   - Usage: `python rename_music_files.py [OPTIONS] PATH`

3. `metadata_audit.py`: Audits and corrects metadata for music files.
   - Checks for missing or inconsistent album-wide metadata
   - Allows batch updating of metadata across an entire album
   - Supports custom album artist categories
   - Usage: `python metadata_audit.py [OPTIONS] LIBRARY_PATH`

Each script supports a `--dry-run` option to simulate actions without making changes, and a `--log-file` option to specify a custom log file location.

### Caution

These scripts modify file structures and metadata. Always back up your music library before running these scripts. Use the `--dry-run` option first to preview changes without modifying files.

### File System Tools

1. `ascii_tree.py`: Prints a directory tree structure in ASCII format.
   - Usage: `python ascii_tree.py [path] [-d DEPTH] [-f]`
   - Options:
     - `path`: Root directory path (default: current directory)
     - `-d DEPTH`, `--depth DEPTH`: Maximum depth of recursion
     - `-f`, `--files`: Include files in the tree (default: directories only)
   - Example: `python ascii_tree.py /home/user/documents -d 3 -f`

### ROM Tools

Located in the `rom_tools` folder, these scripts help manage ROM file collections:

1. `nes_renamer.py`: Renames NES ROM files based on a provided DAT file.
   - Standardizes ROM names according to common databases
   - Handles different region formats (USA, Europe, Japan)
   - Usage: `python nes_renamer.py <input_directory> <dat_file_path>`

2. `rom_copy.py`: Manages ROM file organization and verification.
   - Copies and organizes ROM files based on predefined rules
   - Verifies file integrity during operations
   - Usage: `python rom_copy.py [OPTIONS] SOURCE_DIR DEST_DIR`

### Disc Image Tools

Located in the `disc_tools` folder, these scripts handle disc image management and conversion:

1. `iso_extraction.py`: Extracts ISO files from 7z archives.
   - Handles single and multi-file archives
   - Creates organized output structure
   - Usage: `python iso_extraction.py <folder_path>`

2. `iso_cleanup.py`: Manages ISO files after CHD conversion.
   - Removes ISO files that have corresponding CHD versions
   - Includes dry-run mode for safety
   - Usage: `python iso_cleanup.py <folder_path> [--execute]`

3. `iso_read.py`: Analyzes ISO file headers and structure.
   - Extracts header information
   - Displays hex dumps of critical sections
   - Usage: `python iso_read.py <path_to_iso_file>`

4. `chd_creator.py`: Converts ISO files to CHD format.
   - Batch processes multiple files
   - Utilizes multi-core processing
   - Provides detailed conversion logging
   - Usage: `python chd_creator.py <folder_path>`

All disc tools support graceful interruption and provide detailed logging of operations. The CHD conversion tools require the MAME `chdman` utility to be installed and accessible in the system path.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
