import argparse
from pathlib import Path
import re

def parse_arguments():
    """
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Rename music files by prefixing with track numbers."
    )
    parser.add_argument(
        'path',
        type=str,
        help="Path to the directory containing music files."
    )
    parser.add_argument(
        '--prefix',
        type=str,
        default="1",
        help="Disc number to use in filename (default: '1')."
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Simulate the actions without renaming files."
    )
    parser.add_argument(
        '--auto-clean',
        action='store_true',
        help="Automatically clean filenames of special characters and normalize spacing."
    )
    return parser.parse_args()

def clean_filename(filename):
    """
    Clean filename by removing problematic characters and normalizing spacing.
    """
    # Remove existing track numbers and clean up spaces
    filename = re.sub(r'^\d+\.?\s*-?\s*', '', filename)
    filename = re.sub(r'\s+', ' ', filename).strip()
    
    # Remove or replace problematic characters
    filename = re.sub(r'[\\/*?"<>|]', '', filename)
    
    return filename

def is_audio_file(file_path):
    """
    Check if the file is a recognized audio format.
    """
    audio_extensions = {'.mp3', '.flac', '.m4a', '.opus', '.ogg', '.wav'}
    return file_path.suffix.lower() in audio_extensions

def extract_track_info(filename):
    """
    Extract track number and title from filename.
    Returns tuple of (track_number, title).
    """
    # Common patterns for track numbers
    patterns = [
        r'^(\d+)\s*-\s*(.+)$',      # "01 - Title"
        r'^(\d+)\.\s*(.+)$',        # "01. Title"
        r'^(\d+)\s+(.+)$',          # "01 Title"
    ]
    
    for pattern in patterns:
        match = re.match(pattern, filename)
        if match:
            track_num, title = match.groups()
            return int(track_num), title.strip()
    
    return None, filename

def format_filename(track_num, title, disc_num=None):
    """
    Format filename according to convention: "disc - track. title"
    """
    if track_num is None:
        return title
    
    track_str = str(track_num).zfill(2)
    if disc_num:
        return f"{disc_num.strip()} - {track_str}. {title}"
    return f"{track_str}. {title}"

def rename_files(directory, prefix, dry_run=False, auto_clean=False):
    """
    Iterate through each file in the directory and rename it by adding a prefix.
    """
    directory = Path(directory)
    print(f"Scanning directory: {directory}")
    
    try:
        files = sorted(
            f for f in directory.rglob("*") 
            if f.is_file() and is_audio_file(f) and not f.name.startswith('.')
        )
        print(f"Found {len(files)} audio files")
    except Exception as e:
        print(f"Error accessing directory '{directory}': {e}")
        return

    if not files:
        print("No audio files found to process")
        return

    for file in files:
        original_name = file.name
        name_without_ext, ext = file.stem, file.suffix
        print(f"\nProcessing file: {original_name}")
        print(f"In directory: {file.parent}")
        
        # Extract track number and title
        track_num, title = extract_track_info(name_without_ext)
        
        if auto_clean:
            title = clean_filename(title)
        
        # Format new filename according to convention
        disc_num = prefix if prefix else None
        new_name = format_filename(track_num, title, disc_num) + ext
        new_path = file.parent / new_name
        
        # Skip if the new filename already exists
        if new_path.exists() and new_path != file:
            print(f"  Skipping '{original_name}' as '{new_name}' already exists.")
            continue

        # Show the proposed change
        print(f"About to rename '{original_name}' to '{new_name}'")
        if dry_run:
            print(f"[DRY RUN] Would rename '{original_name}' to '{new_name}'")
            continue
            
        confirm = input("Proceed? (y/n): ").lower()
        if confirm == 'y':
            try:
                file.rename(new_path)
                print(f"Renamed '{original_name}' to '{new_name}'")
            except Exception as e:
                print(f"  Error renaming '{original_name}': {e}")
        else:
            print(f"Skipped renaming '{original_name}'")

def main():
    args = parse_arguments()
    rename_files(
        directory=args.path,
        prefix=args.prefix,
        dry_run=args.dry_run,
        auto_clean=args.auto_clean
    )
    print("\nOperation completed.")

if __name__ == "__main__":
    main()