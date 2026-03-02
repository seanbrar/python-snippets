#!/usr/bin/env python3
"""
Inspect directory names and their character encodings for fuzzy matching.

Useful for diagnosing mismatches caused by Unicode apostrophe variants,
invisible characters, or other encoding quirks in filenames.
"""

import argparse
from pathlib import Path


def normalize_name(name: str) -> str:
    """Normalize a directory name for fuzzy matching."""
    # U+2018 (') and U+2019 (') are curly quotes; U+0027 (') is straight
    normalized = name.replace("\u2018", "'").replace("\u2019", "'").replace("`", "'")
    normalized = normalized.replace(",", "")
    return normalized


def inspect_directory(target_dir: Path, search_name: str | None = None):
    if not target_dir.exists():
        print(f"ERROR: Directory doesn't exist: {target_dir}")
        raise SystemExit(1)

    print(f"Inspecting: {target_dir}")
    print("=" * 80)
    print()

    if search_name:
        target_normalized = normalize_name(search_name)
        print(f"Looking for: '{search_name}'")
        print(f"Normalized:  '{target_normalized}'")
        print(f"Bytes: {search_name.encode('utf-8')}")
        print()
        print("=" * 80)

    print("Directories found:")
    print()

    found_match = False
    for item in sorted(target_dir.iterdir()):
        if not item.is_dir():
            continue

        item_normalized = normalize_name(item.name)
        matches = search_name and item_normalized == normalize_name(search_name)

        print(f"Name:       '{item.name}'")
        print(f"Normalized: '{item_normalized}'")
        print(f"Bytes:      {item.name.encode('utf-8')}")
        print(f"Match:      {matches}")

        if matches:
            found_match = True
            print("\u2713 THIS IS A MATCH!")

        print()

    print("=" * 80)
    if not search_name:
        return

    if found_match:
        print("\u2713 Match found!")
    else:
        print("\u2717 No match found")
        print()
        print("Character-by-character comparison:")
        print()
        for item in target_dir.iterdir():
            if item.is_dir() and search_name.split()[0] in item.name:
                print(f"Target: {search_name!r}")
                print(f"Actual: {item.name!r}")
                print()
                print("Character differences:")
                for i, (c1, c2) in enumerate(zip(search_name, item.name)):
                    if c1 != c2:
                        print(f"  Position {i}: target={c1!r} (U+{ord(c1):04X}) vs actual={c2!r} (U+{ord(c2):04X})")


def main():
    parser = argparse.ArgumentParser(
        description="Inspect directory names and character encodings for fuzzy matching diagnostics."
    )
    parser.add_argument("directory", type=Path, help="Directory to inspect")
    parser.add_argument(
        "-s", "--search",
        help="Subdirectory name to search for (fuzzy-matched against entries)",
    )
    args = parser.parse_args()

    inspect_directory(args.directory, args.search)


if __name__ == "__main__":
    main()
