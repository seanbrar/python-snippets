#!/usr/bin/env python3
import argparse
import logging
import signal
import sys
from datetime import datetime
from pathlib import Path

# Global flag for graceful shutdown
shutdown_requested = False

def setup_logging(base_dir: Path) -> Path:
    """Configure logging to both file and console"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = base_dir / f'cuegen_{timestamp}.log'
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return log_file

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    global shutdown_requested
    logging.info("\nShutdown requested. Completing current operation...")
    shutdown_requested = True

def generate_cue_file(bin_path: Path) -> bool:
    """
    Generate a .cue file for a given .bin file
    Returns True if successful, False otherwise
    """
    try:
        cue_path = bin_path.with_suffix('.cue')
        bin_name = bin_path.name
        
        # Standard PS2 cue file format
        cue_content = f'''FILE "{bin_name}" BINARY
  TRACK 01 MODE2/2352
    INDEX 01 00:00:00
'''
        
        cue_path.write_text(cue_content)
        logging.info(f"Generated cue file: {cue_path}")
        return True
        
    except Exception as e:
        logging.error(f"Failed to generate cue file for {bin_path}: {str(e)}")
        return False

def process_directories(base_dir: Path):
    """Process all subdirectories containing .bin files"""
    # Get all subdirectories
    game_dirs = [d for d in base_dir.iterdir() if d.is_dir()]
    total_dirs = len(game_dirs)
    
    if total_dirs == 0:
        logging.error(f"No subdirectories found in {base_dir}")
        return
    
    logging.info(f"Found {total_dirs} directories to process")
    
    # Statistics
    successful = 0
    failed = 0
    skipped = 0
    interrupted = 0
    
    for index, game_dir in enumerate(game_dirs, 1):
        if shutdown_requested:
            interrupted = total_dirs - (successful + failed + skipped)
            break
        
        logging.info(f"\nProcessing [{index}/{total_dirs}]: {game_dir.name}")
        
        # Find .bin files in this directory
        bin_files = list(game_dir.glob('*.bin'))
        
        if not bin_files:
            logging.warning(f"No .bin files found in {game_dir}")
            skipped += 1
            continue
            
        # Process each .bin file found
        for bin_file in bin_files:
            cue_file = bin_file.with_suffix('.cue')
            
            if cue_file.exists():
                logging.info(f"Cue file already exists for {bin_file.name}, skipping...")
                skipped += 1
                continue
                
            if generate_cue_file(bin_file):
                successful += 1
            else:
                failed += 1
        
        if index % 10 == 0:  # Log progress every 10 directories
            logging.info(f"\nProgress Update:")
            logging.info(f"Processed: {index}/{total_dirs} directories")
            if successful + failed > 0:
                logging.info(f"Success rate: {successful/(successful+failed)*100:.1f}%")
    
    # Log final statistics
    logging.info("\nCue Generation Statistics:")
    logging.info(f"Total directories found: {total_dirs}")
    logging.info(f"Successfully generated: {successful}")
    logging.info(f"Failed generations: {failed}")
    logging.info(f"Skipped (already exist or no .bin): {skipped}")
    if interrupted > 0:
        logging.info(f"Remaining directories (not processed due to shutdown): {interrupted}")

def main():
    parser = argparse.ArgumentParser(description='Generate .cue files for .bin files')
    parser.add_argument('base_dir', help='Base directory containing game subdirectories')
    args = parser.parse_args()
    
    base_dir = Path(args.base_dir)
    
    if not base_dir.is_dir():
        print(f"Error: {base_dir} is not a valid directory")
        sys.exit(1)
    
    # Setup logging
    log_file = setup_logging(base_dir)
    
    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logging.info(f"Starting cue file generation")
    logging.info(f"Base directory: {base_dir}")
    logging.info(f"Log file: {log_file}")
    
    try:
        process_directories(base_dir)
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        if shutdown_requested:
            logging.info("Shutdown complete.")
        else:
            logging.info("Processing complete.")

if __name__ == "__main__":
    main()