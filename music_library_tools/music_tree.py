import os
from pathlib import Path
import argparse
from datetime import datetime
import sys
from typing import TextIO, Optional, Set
import errno

class DirectoryTreeGenerator:
    def __init__(self, output_file: Optional[TextIO] = None, preview_limit: Optional[int] = None):
        """
        Initialize the tree generator with optional file output.
        
        Args:
            output_file: Optional file handle for writing output
            preview_limit: Maximum number of files to show per directory
        """
        self.output_file = output_file
        self.line_count = 0
        self.preview_limit = preview_limit
    
    def write_line(self, line: str) -> None:
        """Write a line to both stdout and file if specified."""
        print(line, file=self.output_file)
        self.line_count += 1
        if self.output_file != sys.stdout:
            print(line)

    def print_directory_tree(self, directory_path: str, prefix: str = "", 
                           is_last: bool = True, exclude_extensions: Optional[Set[str]] = None,
                           max_depth: Optional[int] = None, current_depth: int = 0) -> None:
        """
        Print a tree structure of the given directory path.
        
        Args:
            directory_path: Path to the directory to display
            prefix: Prefix for the current item
            is_last: Boolean indicating if current item is last in its level
            exclude_extensions: Set of file extensions to exclude
            max_depth: Maximum depth to traverse
            current_depth: Current recursion depth
        """
        if exclude_extensions is None:
            exclude_extensions = set()
            
        if max_depth is not None and current_depth > max_depth:
            return
            
        directory = Path(directory_path)
        
        # Print the current directory name
        if prefix == "":  # Root directory
            self.write_line(f"📁 {directory.name}")
        else:
            if is_last:
                self.write_line(f"{prefix}└── 📁 {directory.name}")
            else:
                self.write_line(f"{prefix}├── 📁 {directory.name}")
        
        try:
            items = list(directory.iterdir())
            items.sort(key=lambda x: (not x.is_dir(), x.name.lower()))
        except PermissionError:
            self.write_line(f"{prefix}    ⚠️  Permission denied")
            return
        except Exception as e:
            self.write_line(f"{prefix}    ⚠️  Error: {str(e)}")
            return

        # Separate files and directories
        directories = [item for item in items if item.is_dir()]
        files = [item for item in items if item.is_file()]
        
        # Filter out hidden files and excluded extensions
        files = [f for f in files if not f.name.startswith('.') and 
                not any(f.name.endswith(ext) for ext in exclude_extensions)]
        
        # Handle files with preview limit
        shown_files = files[:self.preview_limit] if self.preview_limit else files
        remaining_files = len(files) - len(shown_files) if self.preview_limit else 0
        
        # Process all items
        total_items = directories + shown_files
        for index, item in enumerate(total_items):
            is_last_item = index == len(total_items) - 1 and remaining_files == 0
            new_prefix = prefix + ("    " if is_last else "│   ")
            
            if item.is_dir():
                self.print_directory_tree(
                    item, new_prefix, is_last_item, exclude_extensions,
                    max_depth, current_depth + 1
                )
            else:
                if is_last_item:
                    self.write_line(f"{prefix}└── 🎵 {item.name}")
                else:
                    self.write_line(f"{prefix}├── 🎵 {item.name}")
        
        # Show count of remaining files if any
        if remaining_files > 0:
            self.write_line(f"{prefix}└── 💿 ... and {remaining_files} more tracks")

def get_output_filename(base_path: str) -> str:
    """Generate a unique filename based on timestamp and directory name."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dir_name = os.path.basename(os.path.normpath(base_path))
    return f"music_tree_{dir_name}_{timestamp}.txt"

def main():
    parser = argparse.ArgumentParser(description='Display a directory tree structure for music files.')
    parser.add_argument('path', help='Path to the music directory')
    parser.add_argument('--exclude', nargs='+', default=['.jpg', '.png', '.txt'],
                       help='File extensions to exclude (default: .jpg .png .txt)')
    parser.add_argument('--output', '-o', help='Output file path (default: auto-generated)')
    parser.add_argument('--max-depth', type=int, help='Maximum depth to traverse')
    parser.add_argument('--no-file', action='store_true', 
                       help='Display output only in terminal without saving to file')
    parser.add_argument('--preview', type=int, metavar='N',
                       help='Show only N files per directory (default: show all)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.path):
        print(f"Error: Path '{args.path}' does not exist")
        return
    
    exclude_extensions = set(ext if ext.startswith('.') else f'.{ext}' for ext in args.exclude)
    
    # Determine output file
    output_file = None
    if not args.no_file:
        output_path = args.output if args.output else get_output_filename(args.path)
        try:
            os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', 
                       exist_ok=True)
            output_file = open(output_path, 'w', encoding='utf-8')
            print(f"\nOutput will be saved to: {output_path}")
        except (OSError, IOError) as e:
            if e.errno == errno.EACCES:
                print(f"Error: Permission denied when trying to create {output_path}")
            else:
                print(f"Error creating output file: {str(e)}")
            return

    try:
        print("\nGenerating directory tree...")
        generator = DirectoryTreeGenerator(
            output_file if output_file else sys.stdout,
            preview_limit=args.preview
        )
        generator.print_directory_tree(
            args.path,
            exclude_extensions=exclude_extensions,
            max_depth=args.max_depth
        )
        print(f"\nProcessed {generator.line_count} items.")
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
    finally:
        if output_file:
            output_file.close()

if __name__ == "__main__":
    main()