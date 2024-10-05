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

### ISO Tools

1. `iso_read.py`: Reads and analyzes the header of an ISO file.
   - Extracts information about unencrypted regions.
   - Displays a hex dump of the ISO header.
   - Usage: `python iso_read.py <path_to_iso_file>`
   - No additional dependencies required.
   - Example: `python iso_read.py /path/to/your/file.iso`

### Game ROM Tools

1. `nes_renamer.py`: Renames NES ROM files based on a provided DAT file.
   - Usage: `python nes_renamer.py <input_directory> <dat_file_path>`
   - Requires no additional dependencies.
   - Example: `python nes_renamer.py /path/to/nes/roms /path/to/nes.dat`
   - Features:
     - Parses DAT files to extract standardized game names
     - Renames NES ROM files to match standardized names
     - Handles different region formats (USA, Europe, Japan)
     - Prevents overwriting existing files
     - Provides detailed logging of the renaming process

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
