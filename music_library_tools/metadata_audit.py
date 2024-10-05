import os
import json
import argparse
from mutagen import File
from colorama import init, Fore, Style, Back

init(autoreset=True)  # Initialize colorama

# Define default log file name
DEFAULT_LOG_FILE = 'metadata_audit_log.json'

# Predefined album artist categories
DEFAULT_CATEGORIES = [
    "Film", "Musical", "Video Game", "Video Game Remix", "Other"
]

# Placeholder for logging issues
log_data = {
    "missing_metadata": [],
    "invalid_metadata": []
}

def parse_arguments():
    """
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Metadata audit and correction for music library."
    )
    parser.add_argument(
        'library_path',
        type=str,
        help="Path to the main music library."
    )
    parser.add_argument(
        '--log-file',
        type=str,
        default=DEFAULT_LOG_FILE,
        help=f"Path to the log file (default: {DEFAULT_LOG_FILE})."
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Simulate the actions without modifying files."
    )
    parser.add_argument(
        '--categories',
        nargs='+',
        default=DEFAULT_CATEGORIES,
        help=f"List of allowed album artist categories (default: {DEFAULT_CATEGORIES})."
    )
    return parser.parse_args()

def audit_album_metadata(root_path, dry_run=False, categories=DEFAULT_CATEGORIES, log_file=DEFAULT_LOG_FILE):
    """
    Check and interactively update metadata at the album level.
    
    Args:
        root_path (str): Path to the root music library.
        dry_run (bool): If True, simulate actions without making changes.
        categories (list): List of allowed album artist categories.
        log_file (str): Path to the log file.
    """
    for root, dirs, files in os.walk(root_path):
        # Only process non-empty folders containing music files
        album_files = [f for f in files if f.lower().endswith(('.mp3', '.flac', '.ogg', '.wav'))]
        if not album_files:
            continue  # Skip empty directories or non-music folders

        print(f"\nProcessing album folder: {os.path.basename(root)}")

        # Initialize album-wide fields
        album_name, album_artist, album_year = None, None, None

        # Collect all metadata across the album
        album_metadata = []
        for file in album_files:
            file_path = os.path.join(root, file)
            try:
                audio = File(file_path, easy=True)
                album = audio.get('album', [None])[0]
                title = audio.get('title', [None])[0]
                album_artist = audio.get('albumartist', [album_artist])[0]  # Preserve the first valid artist found
                year = extract_year(audio)
                album_metadata.append({
                    "file_path": file_path,
                    "album": album,
                    "title": title,
                    "album_artist": album_artist,
                    "year": year
                })

                # Check for missing album-wide fields
                if not album_name and album:
                    album_name = album  # Use the first found album name
                if not album_year and year:
                    album_year = year  # Use the first valid year found
            except Exception as e:
                log_data['invalid_metadata'].append({"file": file_path, "error": str(e)})
                continue

        # Check if album-level fields are missing or inconsistent across the album
        inconsistent_album = any(item['album'] != album_name for item in album_metadata if item['album'])
        inconsistent_year = any(item['year'] != album_year for item in album_metadata if item['year'])
        inconsistent_artist = any(item['album_artist'] != album_artist for item in album_metadata if item['album_artist'])

        # Gather missing or invalid fields for review
        missing_fields = []
        if not album_name or inconsistent_album:
            missing_fields.append("Album Name")
        if not album_artist or album_artist not in categories or inconsistent_artist:
            missing_fields.append("Album Artist")
        if not album_year or inconsistent_year:
            missing_fields.append("Year")

        # Display album-wide metadata issues and prompt for batch update
        if missing_fields:
            print(f"  Issues found for album '{os.path.basename(root)}':")
            print(f"  Current Metadata: Album: '{album_name}', Album Artist: '{album_artist}', Year: '{album_year}'")
            print(f"  Missing/Invalid Fields: {', '.join(missing_fields)}")

            # Prompt the user to correct the album-wide fields
            if "Album Name" in missing_fields:
                album_name = prompt_for_input("Album Name", album_name, dry_run)
            if "Album Artist" in missing_fields:
                album_artist = prompt_for_input(
                    "Album Artist",
                    album_artist,
                    dry_run,
                    allowed_values=categories
                )
            if "Year" in missing_fields:
                album_year = prompt_for_input(
                    "Year (4 digits)",
                    album_year,
                    dry_run,
                    validate_as_year=True
                )

            # Display a preview of the proposed changes for the entire album
            display_proposed_changes(root, album_metadata, album_name, album_artist, album_year)

            # Confirm batch update for all tracks in this album
            while True:
                response = input("\nApply changes for all files in this album? (y = yes, n = no, q = quit): ").strip().lower()
                if response == 'y':
                    if dry_run:
                        print("[DRY RUN] Confirmed. No changes will be made.")
                    else:
                        print("Applying changes...")
                        for item in album_metadata:
                            update_metadata(
                                item['file_path'],
                                album=album_name,
                                artist=album_artist,
                                year=album_year
                            )
                    break
                elif response == 'n':
                    print("Skipping changes for this album.")
                    break
                elif response == 'q':
                    print("Quitting the script.")
                    save_log(log_file)
                    exit(0)
                else:
                    print("Invalid input. Please enter 'y', 'n', or 'q'.")

def update_metadata(file_path, album=None, artist=None, year=None):
    """
    Update metadata fields for a given file.
    
    Args:
        file_path (str): Path to the music file.
        album (str, optional): New album name.
        artist (str, optional): New album artist.
        year (str, optional): New year.
    """
    try:
        audio = File(file_path, easy=True)
        if album:
            audio['album'] = album
        if artist:
            audio['albumartist'] = artist
        if year:
            audio['date'] = year
        audio.save()
        print(f"  Updated metadata for: {file_path}")
    except Exception as e:
        print(f"  Error updating file: {e}")
        log_data['invalid_metadata'].append({"file": file_path, "error": str(e)})

def extract_year(audio_file):
    """
    Extract the year from the 'date' field in metadata.
    If the 'date' field is not four digits or is malformed, return None.
    
    Args:
        audio_file (mutagen.File): The audio file object.
        
    Returns:
        str or None: Extracted year or None if invalid.
    """
    date = audio_file.get('date', [None])[0]
    if date and len(date) >= 4 and date[:4].isdigit():
        return date[:4]  # Extract the first four digits as the year
    return None

def prompt_for_input(field_name, current_value, dry_run, allowed_values=None, validate_as_year=False):
    """
    Prompt the user for input to update a metadata field.
    
    Args:
        field_name (str): The name of the field to update.
        current_value (str): The current value of the field.
        dry_run (bool): If True, simulate the action without making changes.
        allowed_values (list, optional): List of allowed values for validation.
        validate_as_year (bool, optional): If True, validate the input as a four-digit year.
        
    Returns:
        str: The new value entered by the user or the current value if skipped.
    """
    while True:
        prompt_message = f"  Set {field_name} (Current: '{current_value}'): "
        if dry_run:
            prompt_message = f"[DRY RUN] {prompt_message}"
        new_value = input(prompt_message).strip()
        if not new_value:
            print(f"  Skipping {field_name}.")
            return current_value
        if allowed_values and new_value not in allowed_values:
            print(f"  Invalid value for {field_name}. Allowed values: {', '.join(allowed_values)}")
        elif validate_as_year and (not new_value.isdigit() or len(new_value) != 4):
            print(f"  Invalid year format for {field_name}. Please enter a four-digit year (e.g., '2022').")
        else:
            return new_value

def save_log(log_file):
    """
    Save log data to a JSON file for easy inspection.
    
    Args:
        log_file (str): Path to the log file.
    """
    try:
        with open(log_file, 'w') as log:
            json.dump(log_data, log, indent=4)
        print(f"\nLog saved to {log_file}")
    except Exception as e:
        print(f"Error saving log file: {e}")

def highlight_changes(old_value, new_value):
    if old_value != new_value:
        return f"{Fore.RED}{old_value}{Style.RESET_ALL} -> {Fore.GREEN}{new_value}{Style.RESET_ALL}"
    return old_value

def display_proposed_changes(root_path, album_metadata, album_name, album_artist, album_year):
    print(f"\nProposed updates for album '{os.path.basename(root_path)}':")
    print(f"  New Metadata -> Album: '{album_name}', Artist: '{album_artist}', Year: '{album_year}'")
    print("\n  Files to be updated:")
    for item in album_metadata:
        relative_path = os.path.relpath(item['file_path'], root_path)
        truncated_path = truncate_path(relative_path)
        print(f"    {Fore.CYAN}{truncated_path}")
        print(f"      Old -> Album: '{highlight_changes(item['album'], album_name)}', "
              f"Artist: '{highlight_changes(item['album_artist'], album_artist)}', "
              f"Year: '{highlight_changes(item['year'], album_year)}'")
        print(f"      New -> Album: '{album_name}', Artist: '{album_artist}', Year: '{album_year}'")

def truncate_path(path, max_length=50):
    if len(path) <= max_length:
        return path
    parts = path.split(os.sep)
    if len(parts) <= 2:
        return path
    return os.path.join(parts[0], "...", *parts[-2:])

def main():
    args = parse_arguments()
    audit_album_metadata(
        root_path=args.library_path,
        dry_run=args.dry_run,
        categories=args.categories,
        log_file=args.log_file
    )
    save_log(args.log_file)

if __name__ == "__main__":
    main()