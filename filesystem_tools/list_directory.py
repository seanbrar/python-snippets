#!/usr/bin/env python3
"""Recursively list directory contents with configurable depth and item limits."""

import argparse
import os


def list_directory(path, max_depth=3, max_items=10, current_depth=0):
    if current_depth >= max_depth:
        return

    try:
        entries = sorted(os.listdir(path))
    except PermissionError:
        print(f"{'  ' * current_depth}[Permission Denied]: {path}")
        return

    directories = []
    files = []
    for entry in entries:
        full_path = os.path.join(path, entry)
        if os.path.isdir(full_path):
            directories.append(entry)
        else:
            files.append(entry)

    combined = directories + files
    displayed_items = combined[:max_items]
    excluded_count = len(combined) - len(displayed_items)

    indent = '  ' * current_depth
    print(f"{indent}{path} (Excluded: {excluded_count})")

    for item in displayed_items:
        print(f"{indent}  {item}")

    for directory in directories[:max_items]:
        list_directory(os.path.join(path, directory), max_depth, max_items, current_depth + 1)


def main():
    parser = argparse.ArgumentParser(description="Recursively list directory contents.")
    parser.add_argument("path", help="Root directory to list")
    parser.add_argument("-d", "--max-depth", type=int, default=3, help="Maximum recursion depth (default: 3)")
    parser.add_argument("-n", "--max-items", type=int, default=10, help="Maximum items per level (default: 10)")
    args = parser.parse_args()

    if not os.path.isdir(args.path):
        print(f"Error: not a directory: {args.path}")
        raise SystemExit(1)

    list_directory(args.path, max_depth=args.max_depth, max_items=args.max_items)


if __name__ == "__main__":
    main()
