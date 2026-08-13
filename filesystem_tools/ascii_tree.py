import os
import sys
import argparse

def is_windows():
    """Check if the current operating system is Windows."""
    return os.name == 'nt'

def normalize_path(path):
    """
    Normalize path separators for consistent display across platforms.
    
    :param path: The path to normalize
    :return: Normalized path with forward slashes
    """
    return path.replace('\\', '/') if is_windows() else path

def print_tree(root_path, prefix="", max_depth=None, current_depth=0, include_files=True, visited=None):
    """
    Recursively prints the directory tree structure.

    :param root_path: The root directory path to print the tree from.
    :param prefix: The prefix string used for formatting.
    :param max_depth: The maximum depth to recurse into.
    :param current_depth: The current recursion depth.
    :param include_files: Whether to include files in the output.
    :param visited: Set of visited paths to prevent infinite loops with symlinks.
    """
    # Initialize visited set if not provided
    if visited is None:
        visited = set()

    # Check if we've reached the maximum depth
    if max_depth is not None and current_depth > max_depth:
        print(prefix + "└── [Max Depth Reached]")
        return

    try:
        # Get and sort directory entries
        entries = sorted(os.listdir(root_path), key=lambda s: s.lower())
    except PermissionError:
        print(prefix + "└── [Permission Denied]")
        return
    except FileNotFoundError:
        print(prefix + "└── [Path Not Found]")
        return
    except Exception as e:
        print(prefix + f"└── [Error: {e}]")
        return

    directories = []
    files = []

    # Separate directories and files, handling symlinks
    for entry in entries:
        path = os.path.join(root_path, entry)
        if os.path.islink(path):
            # Handle symbolic links
            real_path = os.path.realpath(path)
            if real_path in visited:
                print(prefix + f"└── {entry} -> [Symbolic Link Loop]")
                continue
            visited.add(real_path)
            if os.path.isdir(real_path):
                directories.append(entry)
            elif include_files:
                files.append(entry)
        elif os.path.isdir(path):
            directories.append(entry)
        elif include_files:
            files.append(entry)

    # Combine sorted directories and files
    sorted_entries = directories + files
    entries_count = len(sorted_entries)

    # Print each entry
    for index, entry in enumerate(sorted_entries):
        path = os.path.join(root_path, entry)
        is_last = index == (entries_count - 1)
        connector = "└── " if is_last else "├── "

        if os.path.islink(path):
            # Display symbolic links with their targets
            target = os.readlink(path)
            print(f"{prefix}{connector}{entry} -> {target}")
        else:
            print(f"{prefix}{connector}{entry}")

        if os.path.isdir(path):
            # Recursively print subdirectories
            extension = "    " if is_last else "│   "
            print_tree(path, prefix + extension, max_depth, current_depth + 1, include_files, visited.copy())

def main():
    """
    The main function to parse arguments and initiate the tree printing.
    """
    parser = argparse.ArgumentParser(
        description="Print a visually appealing directory tree structure.",
        epilog="Example: python ascii_tree.py /path/to/directory -d 3 -f"
    )
    parser.add_argument("path", nargs="?", default=".", help="Root directory path")
    parser.add_argument("-d", "--depth", type=int, help="Maximum depth of recursion")
    parser.add_argument("-f", "--files", action="store_true", help="Include files in the tree")
    args = parser.parse_args()

    root = args.path

    # Validate the provided path
    if not os.path.exists(root):
        print(f"Error: The path '{root}' does not exist.")
        sys.exit(1)

    if not os.path.isdir(root):
        print(f"Error: The path '{root}' is not a directory.")
        sys.exit(1)

    # Normalize and display the absolute path
    abs_root = normalize_path(os.path.abspath(root))
    print(f"Directory structure for: {abs_root}")

    # Start printing the tree
    print_tree(abs_root, max_depth=args.depth, include_files=args.files)

if __name__ == "__main__":
    main()
