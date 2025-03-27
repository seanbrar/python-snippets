#!/usr/bin/env python3
import os
import shutil
from pathlib import Path
import argparse
import re
import signal
import sys
import time
import json
from datetime import datetime
from collections import defaultdict

# Global shutdown flag
shutdown_requested = False

# Add this constant at the top of the file, with other constants
IGNORE_EXTENSIONS = {
    # ".ss",  # Save states
    # ".srm",  # Save RAM
    # ".sav",  # Save files
    # ".state",  # Save states
    # ".rtc",  # Real-time clock saves
    # ".m3u",  # Playlists
}


def parse_size_str(size_str):
    """Convert size string like '4.0K' or '1.1G' to bytes with fuzzy matching"""
    units = {"K": 1024, "M": 1024**2, "G": 1024**3, "B": 1}
    match = re.match(r"([\d.]+)([KMGB])", size_str)
    if match:
        num, unit = match.groups()
        return float(num) * units[unit]  # Return as float for fuzzy comparison
    return None


def sizes_match(expected_size, actual_size):
    """Compare sizes with a tolerance percentage"""
    if expected_size is None:
        return True

    # Convert both to float for percentage calculation
    expected = float(expected_size)
    actual = float(actual_size)

    # Calculate percentage difference
    if expected == 0:
        return actual == 0

    diff_percent = abs(expected - actual) / expected * 100
    return diff_percent <= 5  # Allow 5% difference


def apply_path_mappings(file_path, path_mappings, debug=False):
    """Apply path transformations based on mapping rules"""
    original_path = file_path
    for old_path, new_path in path_mappings.items():
        if old_path in file_path:
            file_path = file_path.replace(old_path, new_path)
            if debug:
                print(f"Remapped path:\n  From: {original_path}\n    To: {file_path}")
            break
    return file_path


def should_ignore_file(file_path, ignore_patterns, ignore_extensions=None):
    """Check if file should be ignored based on patterns or extensions"""
    # Check default save file extensions first
    if any(file_path.endswith(ext) for ext in IGNORE_EXTENSIONS):
        return True

    # Then check any additional extensions passed in
    if ignore_extensions and any(file_path.endswith(ext) for ext in ignore_extensions):
        return True

    # Check patterns as before
    for pattern in ignore_patterns:
        # Handle directory patterns (ending with /)
        if pattern.endswith("/"):
            if pattern in file_path:
                return True
        # Handle file extension patterns
        elif pattern.startswith("*."):
            if file_path.endswith(pattern[1:]):
                return True
        # Handle exact matches
        elif pattern in file_path:
            return True
    return False


class CopyStats:
    def __init__(self):
        self.errors = []  # List of (file_path, error_message, error_type) tuples
        self.copied_files = 0
        self.skipped_files = 0
        self.remapped_files = 0
        self.ignored_files = 0  # New counter for ignored files
        self.total_size = 0
        self.start_time = time.time()

    def add_error(self, file_path, error, error_type="general"):
        self.errors.append((file_path, str(error), error_type))

    def print_error_summary(self, output_file=None):
        if not self.errors:
            return

        summary = "\nError Summary:\n"
        summary += "-" * 50 + "\n"
        summary += f"Total Errors: {len(self.errors)}\n\n"

        # Group errors by type first, then by message
        error_types = defaultdict(lambda: defaultdict(list))
        for path, error, error_type in self.errors:
            # Skip known-good "missing" Nintendo retro files
            if error_type == "missing" and any(
                path.startswith(prefix)
                for prefix in ["Nintendo/GB/", "Nintendo/GBC/", "Nintendo/NES/"]
            ):
                continue

            error_types[error_type][error].append(path)

        # Print errors by type, prioritizing missing files
        error_type_order = ["missing", "size_mismatch", "general"]

        for error_type in error_type_order:
            if error_type not in error_types:
                continue

            summary += f"=== {error_type.upper()} Errors ===\n\n"

            for error_msg, paths in error_types[error_type].items():
                summary += f"Error: {error_msg}\n"
                summary += f"Count: {len(paths)}\n\n"

                # Analyze path patterns
                path_components = defaultdict(int)
                for path in paths:
                    dirs = os.path.dirname(path).split(os.sep)
                    for i in range(len(dirs)):
                        path_components[os.sep.join(dirs[: i + 1])] += 1

                # Find directories that contain many errors
                problem_dirs = [
                    (path, count)
                    for path, count in path_components.items()
                    if count > min(5, len(paths) * 0.1)
                ]

                if problem_dirs:
                    summary += "Common problematic directories:\n"
                    for dir_path, count in sorted(
                        problem_dirs, key=lambda x: x[1], reverse=True
                    ):
                        summary += f"  - {dir_path}: {count} files\n"
                    summary += "\n"

                # Show sample files
                summary += "Sample affected files:\n"
                sample_size = min(20, len(paths))
                for path in paths[:sample_size]:
                    summary += f"  - {path}\n"
                if len(paths) > sample_size:
                    summary += f"  ... and {len(paths)-sample_size} more files\n"
                summary += "\n"

        if output_file:
            with open(output_file, "w") as f:
                f.write(summary)
        print(summary, flush=True)


def signal_handler(signum, frame):
    """Handle shutdown signal"""
    global shutdown_requested
    print(
        "\nShutdown requested... Will stop after current file copy completes.",
        flush=True,
    )
    shutdown_requested = True


def parse_inventory(inventory_path, debug=False):
    """Parse the inventory file and return a list of (file_path, expected_size) tuples."""
    files = []
    path_components = []
    base_depth = None

    with open(inventory_path, "r") as f:
        # Skip header until we find "Directory Structure:"
        for line in f:
            if "Directory Structure:" in line:
                break

        # Process file structure
        for line in f:
            line = line.rstrip()
            if not line or line.isspace():
                continue

            indent = len(line) - len(line.lstrip())
            depth = indent // 2
            entry = line.strip()

            if entry.startswith("[DIR]"):
                dir_name = entry[5:].strip()

                if base_depth is None:
                    base_depth = depth

                if depth == base_depth:
                    path_components = [dir_name]
                else:
                    relative_depth = depth - base_depth
                    path_components = path_components[:relative_depth]
                    path_components.append(dir_name)

                if debug:
                    print(f"DIR: {os.path.join(*path_components)}")

            elif entry.startswith("[FILE]"):
                size_match = re.match(r"\[FILE\]\s*\(([^)]+)\)\s*(.+)$", entry)
                if size_match:
                    size_str, filename = size_match.groups()
                    filename = filename.strip()
                    if path_components:
                        full_path = os.path.join(*path_components, filename)
                    else:
                        full_path = filename
                    files.append((full_path, size_str))

                    if debug:
                        print(f"FILE: {full_path} ({size_str})")

    return files


def format_size(size):
    """Convert bytes to human readable format."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"


def print_progress(copied_files, total_files, total_size, start_time, clear_line=True):
    """Print progress information."""
    elapsed = time.time() - start_time
    files_per_sec = copied_files / elapsed if elapsed > 0 else 0

    if clear_line:
        print("\r" + " " * 80 + "\r", end="")

    print(
        f"Progress: {copied_files}/{total_files} files "
        + f"({(copied_files/total_files*100):.1f}%) | "
        + f"Size: {format_size(total_size)} | "
        + f"Rate: {files_per_sec:.1f} files/sec",
        end="\r" if clear_line else "\n",
        flush=True,
    )


def print_final_summary(stats, total_files):
    """Print final summary of the operation."""
    elapsed = time.time() - stats.start_time
    files_per_sec = stats.copied_files / elapsed if elapsed > 0 else 0

    print(f"\n\nOperation completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Files processed: {stats.copied_files}/{total_files}")
    print(f"Files skipped: {stats.skipped_files} (already existed)")
    print(f"Files ignored: {stats.ignored_files} (matched ignore patterns)")
    print(f"Files remapped: {stats.remapped_files}")
    print(f"Files with errors: {len(stats.errors)}")
    print(f"Total size: {format_size(stats.total_size)}")
    print(f"Elapsed time: {elapsed:.1f} seconds")
    print(f"Average rate: {files_per_sec:.1f} files/sec")
    print("-" * 50, flush=True)


def copy_roms(
    inventory_path,
    source_base,
    dest_base,
    path_mappings=None,
    ignore_patterns=None,
    ignore_extensions=None,
    dry_run=True,
    verbose=True,
    errors_only=False,
    debug=False,
):
    """Copy ROMs from source to destination based on inventory."""
    stats = CopyStats()
    file_entries = parse_inventory(inventory_path, debug)
    total_files = len(file_entries)
    last_update = stats.start_time
    update_interval = 1.0  # Status update every second

    if path_mappings is None:
        path_mappings = {}
    if ignore_patterns is None:
        ignore_patterns = []
    if ignore_extensions is None:
        ignore_extensions = []

    if not errors_only:
        print(
            f"\nStarting copy operation at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        print(f"Total files to process: {total_files}")
        print("-" * 50, flush=True)

    for file_path, expected_size_str in file_entries:
        if shutdown_requested:
            print("\nStopping copy operation...")
            break

        # Check ignore conditions first
        if should_ignore_file(file_path, ignore_patterns, ignore_extensions):
            stats.ignored_files += 1
            if debug:
                print(f"Ignoring file: {file_path}")
            continue

        # Apply path mapping before constructing source path
        mapped_path = apply_path_mappings(file_path, path_mappings, debug)
        if mapped_path != file_path:
            stats.remapped_files += 1
            if debug:
                print(f"Remapped path:\n  From: {file_path}\n    To: {mapped_path}")

        expected_size = parse_size_str(expected_size_str)
        source = os.path.join(source_base, mapped_path)
        dest = os.path.join(dest_base, file_path)  # Use original path for destination
        dest_dir = os.path.dirname(dest)

        if dry_run:
            print(f"Would copy: {source}")
            print(f"       to: {dest}")
            print(f"   making: {dest_dir}")
            print("---", flush=True)
            continue

        try:
            # Check if source exists
            if not os.path.exists(source):
                stats.add_error(
                    file_path,
                    f"Source file not found (expected size: {expected_size_str})",
                    "missing",
                )
                continue

            # Get source file size and validate
            actual_size = os.path.getsize(source)
            if expected_size and not sizes_match(expected_size, actual_size):
                stats.add_error(
                    file_path,
                    f"Size mismatch - Expected: {expected_size_str}, Found: {format_size(actual_size)}",
                    "size_mismatch",
                )
                continue

            # Check if destination exists with same size
            if os.path.exists(dest) and os.path.getsize(dest) == actual_size:
                if verbose and not errors_only:
                    print(f"\nSkipping (already exists): {file_path}", flush=True)
                stats.skipped_files += 1
                stats.copied_files += 1
                stats.total_size += actual_size
                continue

            # Create destination directory if needed
            os.makedirs(dest_dir, exist_ok=True)

            # Print current file (with progress on next line)
            if not errors_only:
                print_progress(
                    stats.copied_files,
                    total_files,
                    stats.total_size,
                    stats.start_time,
                    clear_line=True,
                )
                print(f"\nCopying: {file_path}", flush=True)

            # Perform the copy
            shutil.copy2(source, dest)

            stats.copied_files += 1
            stats.total_size += actual_size

            # Update progress periodically
            current_time = time.time()
            if current_time - last_update >= update_interval and not errors_only:
                print_progress(
                    stats.copied_files,
                    total_files,
                    stats.total_size,
                    stats.start_time,
                    clear_line=True,
                )
                last_update = current_time

        except Exception as e:
            stats.add_error(file_path, e, "general")
            if not errors_only:
                print(f"\nError copying {file_path}: {str(e)}", flush=True)

    # Print final summary
    if not errors_only or stats.errors:
        print_final_summary(stats, total_files)
        stats.print_error_summary()

    return stats


def main():
    parser = argparse.ArgumentParser(description="Copy ROMs based on inventory file")
    parser.add_argument("inventory", help="Path to the inventory file")
    parser.add_argument("source", help="Base path of source ROMs")
    parser.add_argument("destination", help="Base path for ROM copies")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute the copy (without this flag, does a dry run)",
    )
    parser.add_argument("--quiet", action="store_true", help="Reduce output verbosity")
    parser.add_argument(
        "--errors-only",
        action="store_true",
        help="Only show error messages during operation",
    )
    parser.add_argument("--error-log", help="Write error details to specified file")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug output during inventory parsing",
    )
    parser.add_argument("--path-mappings", help="JSON file containing path mappings")
    parser.add_argument(
        "--ignore-patterns", help="JSON file containing ignore patterns"
    )

    args = parser.parse_args()

    # Load path mappings if provided
    path_mappings = {}
    if args.path_mappings:
        try:
            with open(args.path_mappings, "r") as f:
                path_mappings = json.load(f)
        except Exception as e:
            print(f"Error loading path mappings: {str(e)}")
            sys.exit(1)

    # Load ignore patterns if provided
    ignore_patterns = []
    if args.ignore_patterns:
        try:
            with open(args.ignore_patterns, "r") as f:
                config = json.load(f)
                ignore_patterns = config.get("ignore_patterns", [])
        except Exception as e:
            print(f"Error loading ignore patterns: {str(e)}")
            sys.exit(1)

    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)

    # Disable output buffering
    if sys.stdout.isatty():
        sys.stdout.reconfigure(line_buffering=True)

    try:
        stats = copy_roms(
            args.inventory,
            args.source,
            args.destination,
            path_mappings=path_mappings,
            ignore_patterns=ignore_patterns,
            dry_run=not args.execute,
            verbose=not args.quiet,
            errors_only=args.errors_only,
            debug=args.debug,
        )

        if args.error_log:
            print(f"\nWriting error log to: {args.error_log}")
            stats.print_error_summary(args.error_log)
            print(f"Error log written: {os.path.exists(args.error_log)}")

    except KeyboardInterrupt:
        print("\nOperation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
