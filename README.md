# Python Snippets

[![MIT License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Python 3.x](https://img.shields.io/badge/python-3.x-blue.svg)](https://www.python.org/downloads/)

A collection of Python utility scripts for text extraction, media management, file system tools, and more.

## Quick Reference

Every script in the repo, searchable by what it does.

| Script | What it does | Keywords |
|--------|-------------|----------|
| [`pdf_extractor.py`](text_extraction/pdf_extractor.py) | Extract text from PDFs with structure, columns, and tables | pdf, text, extract, poppler, pdfplumber |
| [`epub_extractor.py`](text_extraction/epub_extractor.py) | Extract chapters from ePub files to text/Markdown/HTML | epub, ebook, chapters, markdown |
| [`cite_regex.py`](text_extraction/cite_regex.py) | Remove citation markers (`[1]`, `[2]`) from text | citations, regex, brackets, clean |
| [`concat_markdown.py`](text_extraction/concat_markdown.py) | Concatenate `.md` files in a directory into one file | markdown, merge, combine |
| [`ascii_tree.py`](filesystem_tools/ascii_tree.py) | Print a directory tree in ASCII format | tree, directory, listing, ascii |
| [`list_directory.py`](filesystem_tools/list_directory.py) | Recursively list directory contents with depth limits | directory, list, recursive |
| [`diagnostic_directory.py`](filesystem_tools/diagnostic_directory.py) | Inspect filenames for Unicode/encoding mismatches | unicode, encoding, filenames, curly quotes |
| [`rename_music_files.py`](music_library_tools/rename_music_files.py) | Rename music files by disc/track number | music, rename, tracks, disc |
| [`music_tree.py`](music_library_tools/music_tree.py) | Print a music library directory tree | music, tree, listing |
| [`music_reorganizer.py`](music_library_tools/music_reorganizer.py) | Reorganize music files by metadata (artist/album) | music, organize, metadata, artist, album |
| [`metadata_audit.py`](music_library_tools/metadata_audit.py) | Audit and correct music file metadata | music, metadata, audit, tags |
| [`nes_renamer.py`](rom_tools/nes_renamer.py) | Rename NES ROMs using a No-Intro DAT file | nes, roms, rename, no-intro, dat |
| [`rom_copy.py`](rom_tools/rom_copy.py) | Copy and organize ROM files with path mappings | roms, copy, organize, mappings |
| [`iso_extraction.py`](disc_tools/iso_extraction.py) | Extract ISO files from 7z archives | iso, 7z, extract, disc |
| [`chd_creator.py`](disc_tools/chd_creator.py) | Batch convert ISO to CHD format | iso, chd, convert, mame, chdman |
| [`iso_cleanup.py`](disc_tools/iso_cleanup.py) | Remove ISOs after CHD conversion | iso, chd, cleanup, delete |
| [`iso_read.py`](disc_tools/iso_read.py) | Analyze ISO file headers and structure | iso, headers, inspect, read |
| [`bin_to_chd.py`](disc_tools/bin_to_chd.py) | BIN/CUE to CHD conversion pipeline | bin, cue, chd, convert |
| [`transcript_elevenlabs.py`](misc/transcript_elevenlabs.py) | Transcribe video/audio via ElevenLabs API | transcribe, audio, video, elevenlabs, speech-to-text |
| [`ups_value.py`](misc/ups_value.py) | Evaluate UPS fit for a given load (watts, VA, runtime) | ups, power, watts, battery, sizing |
| [`ac_value_calcs.py`](misc/ac_value_calcs.py) | Calculate AC/SEER energy savings and ROI | ac, hvac, seer, energy, savings, roi |
| [`base64_convert.py`](misc/base64_convert.py) | Decode base64 and parse ASN.1 for ECDSA r/s values | base64, asn1, ecdsa, cryptography |
| [`elements_code.py`](misc/elements_code.py) | Extract metadata from Elements-style JSON exports | elements, metadata, json |

## Directory Structure

```
python-snippets/
├── text_extraction/      PDF, ePub, and Markdown processing
├── filesystem_tools/     Directory inspection and visualization
├── music_library_tools/  Music file organization and metadata
├── rom_tools/            ROM file management and renaming
├── disc_tools/           Disc image (ISO/CHD) tools
└── misc/                 Standalone one-off utilities
```

Each subdirectory has its own README with detailed usage instructions.

## Install

1. Clone the repository:
   ```bash
   git clone https://github.com/seanbrar/python-snippets.git
   cd python-snippets
   ```

2. Install dependencies for the tools you need:
   ```bash
   pip install -r text_extraction/requirements.txt   # PDF and ePub extraction
   pip install -r music_library_tools/requirements.txt  # Music library tools
   pip install -r misc/requirements.txt              # ElevenLabs transcription
   pip install py7zr                                  # Disc image extraction
   ```

   Most scripts in `filesystem_tools/`, `rom_tools/`, and several in `misc/` need only Python 3.x.

## Usage

Each script can be run independently from the repo root:

```bash
python <category>/script_name.py [OPTIONS] [ARGUMENTS]
```

See the README in each subdirectory for detailed usage.

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
