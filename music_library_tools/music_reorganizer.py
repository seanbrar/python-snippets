import os
import shutil
import json
import argparse
import re
from mutagen import File
from colorama import init, Fore, Style, Back
import logging

init(autoreset=True)  # Initialize colorama

# Define default log file name
DEFAULT_LOG_FILE = "music_reorg_log.json"

# Placeholder for logging issues
log_data = {
    "missing_metadata": [],
    "invalid_filenames": [],
    "invalid_folders": [],
    "invalid_date_metadata": [],
}

# Configure logging for debugging purposes
# logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")


def parse_arguments():
    """
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(description="Reorganize music library.")
    parser.add_argument(
        "library_path", type=str, help="Path to the main music library."
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default=DEFAULT_LOG_FILE,
        help=f"Path to the log file (default: {DEFAULT_LOG_FILE}).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate the actions without modifying files.",
    )
    return parser.parse_args()


def sanitize_filename(filename):
    """
    Sanitize the filename by removing or replacing problematic characters.

    Args:
        filename (str): The original filename.

    Returns:
        str: The sanitized filename.
    """
    # Replace forward slashes with hyphens
    filename = filename.replace("/", "-")

    # Remove or replace other potentially problematic characters
    filename = re.sub(r'[<>:"|?*]', "", filename)

    # Remove leading/trailing periods and spaces
    filename = filename.strip(". ")

    return filename


def clean_album_name(name):
    """
    Clean the album name by removing unwanted terms and characters.

    Args:
        name (str): The original album name.

    Returns:
        str: The cleaned album name.
    """
    # Remove terms like "Soundtrack", "OST", etc.
    terms_to_remove = [
        r"\bOST\b",
        r"\bSoundtrack\b",
        r"\bOriginal Motion Picture Soundtrack\b",
        r"\bOriginal Soundtrack\b",
    ]
    for term in terms_to_remove:
        name = re.sub(term, "", name, flags=re.IGNORECASE).strip()

    # Remove any unwanted characters but preserve brackets that likely contain artist names
    # Modify the regex to only remove leading/trailing parentheses, dashes, or braces,
    # but not brackets if they are part of the artist's name.
    # For example, preserve ']' if it follows a '['
    name = re.sub(
        r"^[\s\-\(\{\[]+|[\s\-\)\}\]]+$",
        lambda match: match.group(0) if match.group(0) in ["[", "]"] else "",
        name,
    )

    return name.strip()


def construct_album_folder_name(album, format_type, year):
    """
    Construct a properly formatted album folder name.

    Args:
        album (str): The album name retrieved from metadata. Expected to include artist in brackets, e.g., "Project Chaos [NiGHTS]".
        format_type (str): The audio format (e.g., 'FLAC').
        year (str): The album year.

    Returns:
        str: The formatted album folder name, e.g., "Project Chaos [NiGHTS] (FLAC) [2011]"
    """
    # logging.debug(f"Original album name: '{album}'")

    # Step 1: Remove existing format and year information if present
    # This regex removes patterns like " (FLAC) [2013]" at the end of the string
    album_cleaned = re.sub(r"\s*\([^)]*\)\s*\[\d{4}\]$", "", album)
    # logging.debug(f"Album after removing existing format/year: '{album_cleaned}'")

    # Step 2: Prepare the additional information to append
    additional_info = f"({format_type})"
    if year:
        additional_info += f" [{year}]"
    # logging.debug(f"Additional info to append: '{additional_info}'")

    # Step 3: Check if the album name contains an artist in brackets
    match = re.match(r"^(.*?)\s*\[(.*?)\]$", album_cleaned)
    if match:
        album_name = match.group(1).strip()
        artist = match.group(2).strip()
        # logging.debug(f"Detected album name: '{album_name}', artist: '{artist}'")

        # Step 4: Reconstruct the album folder name
        new_album = f"{album_name} [{artist}] {additional_info}"
        # logging.debug(f"Reconstructed album folder name: '{new_album}'")
    else:
        # If no artist bracket is found, append the additional info directly
        new_album = f"{album_cleaned} {additional_info}"
        # logging.debug(f"No artist bracket detected. Appended additional info: '{new_album}'")

    # Step 5: Sanitize the final album folder name
    sanitized_album = sanitize_filename(new_album)
    # logging.debug(f"Sanitized album folder name: '{sanitized_album}'")

    return sanitized_album


def parse_filename(filename):
    """
    Parse and validate filenames to extract disc number, track number, and title.

    Args:
        filename (str): The original filename.

    Returns:
        tuple: (disc_number, track_number, original_title, extension)
    """
    name_without_ext, ext = os.path.splitext(filename)

    # Primary pattern: disc - track - title
    match = re.match(r"^(\d+)\s*-\s*(\d+)\s*-\s*(.+)$", name_without_ext)
    if match:
        disc_num, track_num, title = match.groups()
        title = title.lstrip(" -.")  # Remove leading spaces, dashes, or dots
        return disc_num, track_num, title.strip(), ext

    # Secondary pattern: disc - track.title (handles variations)
    match = re.match(r"^(\d+)\s*-\s*(\d+)\s*[.-]\s*(.+)$", name_without_ext)
    if match:
        disc_num, track_num, title = match.groups()
        title = title.lstrip(" -.")  # Remove leading spaces, dashes, or dots
        return disc_num, track_num, title.strip(), ext

    # If no pattern matches, return defaults
    return "0", "00", name_without_ext.strip(), ext


def move_all_contents(src, dst):
    """
    Move all files and subfolders from the source to the destination directory.

    Args:
        src (str): Source directory path.
        dst (str): Destination directory path.
    """
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.move(s, d)
        else:
            shutil.move(s, d)


def highlight_filename_changes(old_name, new_name):
    if old_name != new_name:
        return f"{Fore.RED}{old_name}{Style.RESET_ALL} -> {Fore.GREEN}{new_name}{Style.RESET_ALL}"
    return f"{Fore.YELLOW}{old_name}"  # Yellow for unchanged files


def display_proposed_changes(
    root_path, current_album_name, new_album_name, proposed_changes
):
    print(f"\nProcessing album: {Fore.CYAN}{current_album_name}")

    if current_album_name != new_album_name:
        print(f"Proposed rename: {Fore.GREEN}{new_album_name}")

    if not proposed_changes:
        print(f"  {Fore.YELLOW}No changes needed for this album.")
        return

    print("\nProposed changes:")
    current_folder = None
    for before, after in proposed_changes:
        before_rel = os.path.relpath(before, root_path)
        after_rel = os.path.relpath(after, root_path)

        before_folder = os.path.dirname(before_rel)
        after_folder = os.path.dirname(after_rel)

        if before_folder != current_folder:
            if current_folder is not None:
                print()  # Add a newline between folders
            print(f"  {Fore.CYAN}{before_folder}/")
            if before_folder != after_folder:
                print(f"  {Fore.GREEN}-> {after_folder}/")
            current_folder = before_folder

        before_file = os.path.basename(before_rel)
        after_file = os.path.basename(after_rel)
        if before_file != after_file:
            print(f"    {highlight_filename_changes(before_file, after_file)}")


def truncate_path(path, max_length=50):
    if len(path) <= max_length:
        return path
    parts = path.split(os.sep)
    if len(parts) <= 2:
        return path
    return os.path.join(parts[0], "...", *parts[-2:])


def save_log(log_file):
    """
    Save log data to a JSON file for easy inspection.

    Args:
        log_file (str): Path to the log file.
    """
    try:
        with open(log_file, "w") as log:
            json.dump(log_data, log, indent=4)
        print(f"\nLog saved to {log_file}")
    except Exception as e:
        print(f"Error saving log file: {e}")


def extract_year(audio_file):
    """
    Extract the year from the 'date' field in metadata.
    If the 'date' field is not four digits or is malformed, return None.

    Args:
        audio_file (mutagen.File): The audio file object.

    Returns:
        str or None: Extracted year or None if invalid.
    """
    date = audio_file.get("date", [None])[0]
    if date and len(date) >= 4 and date[:4].isdigit():
        return date[:4]  # Take only the first four digits as year
    else:
        # Log the issue if the date is invalid
        log_data["invalid_date_metadata"].append(
            {
                "file": audio_file.filename,
                "date_field": date,
                "message": "Invalid or missing date field",
            }
        )
        return None


def reorganize_album(root_path, dry_run=False, log_file=DEFAULT_LOG_FILE):
    """
    Parse and organize albums by album.

    Args:
        root_path (str): Path to the root music library.
        dry_run (bool): If True, simulate actions without making changes.
        log_file (str): Path to the log file.
    """
    for root, dirs, files in os.walk(root_path, topdown=False):
        if root == root_path:
            # Skip the root directory itself
            continue

        album_files = [
            f for f in files if f.lower().endswith((".mp3", ".flac", ".ogg", ".wav"))
        ]
        if not album_files:
            continue  # Skip empty directories or non-music folders

        # Create a list to track file movements
        proposed_changes = []

        # Extract common metadata for the album
        sample_file = os.path.join(root, album_files[0])
        try:
            audio = File(sample_file, easy=True)
            album = audio.get("album", ["Unknown Album"])[0]
            year = extract_year(audio)
            format_type = os.path.splitext(sample_file)[1][1:].upper()
        except Exception as e:
            log_data["invalid_filenames"].append({"file": sample_file, "error": str(e)})
            continue

        # Clean the album name
        album = clean_album_name(album)

        # Construct new album folder name
        album_name = construct_album_folder_name(album, format_type, year)

        # Preserve the parent folder structure
        relative_path = os.path.relpath(root, root_path)
        parent_folder = os.path.dirname(relative_path)
        target_dir = os.path.join(root_path, parent_folder, album_name)

        # Process each file in the album
        for file in album_files:
            file_path = os.path.join(root, file)
            try:
                disc_number, track_number, original_title, ext = parse_filename(file)

                # Construct the new filename
                new_filename = f"{disc_number} - {track_number}. {original_title}{ext}"
                new_file_path = os.path.join(target_dir, new_filename)

                if os.path.abspath(file_path) != os.path.abspath(new_file_path):
                    proposed_changes.append((file_path, new_file_path))
            except Exception as e:
                log_data["invalid_filenames"].append(
                    {"file": file_path, "error": str(e)}
                )

        # Present and confirm changes
        current_album_name = os.path.basename(root)
        if proposed_changes:
            display_proposed_changes(
                root_path, current_album_name, album_name, proposed_changes
            )

            while True:
                response = (
                    input("\nConfirm changes? (y = yes, n = no, q = quit): ")
                    .strip()
                    .lower()
                )
                if response == "y":
                    if dry_run:
                        print("[DRY RUN] Confirmed. No changes will be made.")
                    else:
                        print("Applying changes...")
                        os.makedirs(target_dir, exist_ok=True)
                        for before, after in proposed_changes:
                            shutil.move(before, after)
                            print(f"  Moved: {before} -> {after}")

                        # Move remaining files and subfolders
                        move_all_contents(root, target_dir)

                        # Remove the old folder
                        try:
                            os.rmdir(root)
                            print(f"  Removed empty folder: {root}")
                        except OSError:
                            print(
                                f"  Warning: Could not remove folder {root}. It may not be empty."
                            )
                    break
                elif response == "n":
                    print("Skipping album changes.")
                    break
                elif response == "q":
                    print("Quitting the script.")
                    save_log(log_file)
                    exit(0)
                else:
                    print("Invalid input. Please enter 'y', 'n', or 'q'.")
        else:
            print(f"\nProcessing album: {Fore.CYAN}{current_album_name}")
            print(f"  {Fore.YELLOW}No changes needed for this album.")


def main():
    args = parse_arguments()
    reorganize_album(
        root_path=args.library_path, dry_run=args.dry_run, log_file=args.log_file
    )
    save_log(args.log_file)


if __name__ == "__main__":
    main()