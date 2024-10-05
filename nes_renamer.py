import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
import logging
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def parse_dat(dat_path):
    """
    Parse the DAT XML file to extract game names and corresponding ROM names.
    The DAT file contains standardized information about NES games and ROMs.

    Args:
        dat_path (Path): Path to the DAT file.

    Returns:
        dict: A dictionary mapping game names to ROM names.
    """
    try:
        # Attempt to parse the XML file
        tree = ET.parse(dat_path)
    except ET.ParseError as e:
        logging.error(f"Error parsing DAT file: {e}")
        sys.exit(1)
    except FileNotFoundError:
        logging.error(f"DAT file not found: {dat_path}")
        sys.exit(1)
    
    root = tree.getroot()
    game_names = {}
    # Iterate through all 'game' elements in the XML
    for game in root.findall('.//game'):
        name = game.get('name')
        rom = game.find('rom')
        if rom is not None:
            rom_name = rom.get('name')
            game_names[name] = rom_name
    return game_names

def rename_roms(input_dir, dat_path):
    """
    Rename NES ROM files in the input directory based on the DAT file.
    This function processes each .nes file in the input directory and attempts to rename it
    according to the standardized names from the DAT file.

    Args:
        input_dir (str): Path to the directory containing NES ROM files.
        dat_path (str): Path to the DAT file.
    """
    input_path = Path(input_dir)
    dat_path = Path(dat_path)
    
    if not input_path.is_dir():
        logging.error(f"Input directory does not exist: {input_dir}")
        sys.exit(1)
    
    game_names = parse_dat(dat_path)
    
    for file in input_path.iterdir():
        if file.suffix.lower() == '.nes':
            # This regex extracts the game name and region code from the filename
            match = re.match(r'^(.*?)\s*\(([UuEeJj])\)$', file.stem)
            if match:
                game_name, region = match.groups()
                region = region.upper()
                
                # Convert region code to full name for DAT file matching
                region_full = {'U': 'USA', 'E': 'Europe', 'J': 'Japan'}.get(region, 'Unknown')
                dat_name = f"{game_name} ({region_full})"
                
                if dat_name in game_names:
                    new_filename = game_names[dat_name]
                    new_file = input_path / new_filename
                    
                    # Prevent overwriting existing files
                    if new_file.exists():
                        logging.warning(f"Cannot rename {file.name} to {new_filename}: Destination file already exists.")
                        continue
                    
                    try:
                        file.rename(new_file)
                        logging.info(f"Renamed: {file.name} -> {new_filename}")
                    except Exception as e:
                        logging.error(f"Failed to rename {file.name}: {e}")
                else:
                    logging.warning(f"No match found for: {file.name}")
            else:
                logging.warning(f"Filename format not recognized: {file.name}")

def main():
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description="Rename NES ROM files based on a DAT file.")
    parser.add_argument('input_dir', help="Path to the directory containing NES ROM files.")
    parser.add_argument('dat_path', help="Path to the DAT file.")
    
    args = parser.parse_args()
    
    # Execute the main renaming function with provided arguments
    rename_roms(args.input_dir, args.dat_path)

if __name__ == "__main__":
    main()