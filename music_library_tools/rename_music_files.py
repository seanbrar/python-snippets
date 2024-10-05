import os
import argparse

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
        default="1 - ",
        help="Prefix to add to each filename (default: '1 - ')."
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Simulate the actions without renaming files."
    )
    return parser.parse_args()

def rename_files(directory, prefix, dry_run=False):
    """
    Iterate through each file in the directory and rename it by adding a prefix.
    
    Args:
        directory (str): Path to the directory containing music files.
        prefix (str): Prefix to add to each filename.
        dry_run (bool): If True, simulate actions without renaming files.
    """
    try:
        files = os.listdir(directory)
    except FileNotFoundError:
        print(f"Error: The directory '{directory}' does not exist.")
        return
    except PermissionError:
        print(f"Error: Permission denied for directory '{directory}'.")
        return

    for file in files:
        file_path = os.path.join(directory, file)
        # Check if it's a file (not a directory)
        if os.path.isfile(file_path):
            new_name = f"{prefix}{file}"
            new_file_path = os.path.join(directory, new_name)
            
            # Skip if the new filename already exists to prevent overwriting
            if os.path.exists(new_file_path):
                print(f"  Skipping '{file}' as '{new_name}' already exists.")
                continue

            # Ask for confirmation before renaming
            print(f"About to rename '{file}' to '{new_name}'")
            confirm = input("Proceed? (y/n): ").lower()
            
            if confirm == 'y':
                if dry_run:
                    print(f"[DRY RUN] Would rename '{file}' to '{new_name}'")
                else:
                    try:
                        os.rename(file_path, new_file_path)
                        print(f"Renamed '{file}' to '{new_name}'")
                    except Exception as e:
                        print(f"  Error renaming '{file}': {e}")
            else:
                print(f"Skipped renaming '{file}'")

def main():
    args = parse_arguments()
    rename_files(
        directory=args.path,
        prefix=args.prefix,
        dry_run=args.dry_run
    )
    print("Operation completed.")

if __name__ == "__main__":
    main()