#!/usr/bin/env python3

import os
import sys
import glob

def concatenate_markdown_files(input_dir, output_file):
    """
    Concatenate all markdown files in the input directory into a single output file.
    
    Args:
        input_dir (str): Path to the directory containing markdown files
        output_file (str): Path to the output file
    """
    # Make sure the input directory exists
    if not os.path.isdir(input_dir):
        print(f"Error: Directory '{input_dir}' not found.")
        sys.exit(1)
    
    # Find all markdown files in the directory
    markdown_files = glob.glob(os.path.join(input_dir, "*.md"))
    
    if not markdown_files:
        print(f"No markdown files found in '{input_dir}'.")
        sys.exit(0)
    
    # Sort the files alphabetically
    markdown_files.sort()
    
    print(f"Found {len(markdown_files)} markdown files. Concatenating...")
    
    # Open the output file
    with open(output_file, 'w', encoding='utf-8') as outfile:
        # Write a header to the output file
        outfile.write(f"# Concatenated Markdown Files from {os.path.basename(input_dir)}\n\n")
        
        # Process each markdown file
        for md_file in markdown_files:
            filename = os.path.basename(md_file)
            print(f"Processing: {filename}")
            
            # Add a separator and filename before each file's content
            outfile.write(f"## From file: {filename}\n\n")
            
            # Read and write the content of the file
            try:
                with open(md_file, 'r', encoding='utf-8') as infile:
                    outfile.write(infile.read())
                # Add newlines between files
                outfile.write("\n\n")
            except Exception as e:
                print(f"Error reading file {filename}: {e}")
    
    print(f"Concatenation complete. Output saved to '{output_file}'")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python concat_markdown.py <input_directory> <output_file>")
        sys.exit(1)
    
    input_dir = sys.argv[1]
    output_file = sys.argv[2]
    
    concatenate_markdown_files(input_dir, output_file)