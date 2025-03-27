#!/usr/bin/env python3
import argparse
import logging
import os
import signal
import sys
from datetime import datetime
from pathlib import Path
import py7zr
import shutil

# Global flag for graceful shutdown
shutdown_requested = False

def setup_logging(output_dir: Path) -> Path:
    """Configure logging to both file and console"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = output_dir / f'extraction_{timestamp}.log'
    
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

def extract_archive(archive_path: Path, output_dir: Path) -> bool:
    """
    Extract a .7z archive to its own subdirectory
    Returns True if successful, False otherwise
    """
    try:
        # Create subdirectory with same name as archive (minus .7z extension)
        subdir = output_dir / archive_path.stem
        subdir.mkdir(exist_ok=True)
        
        with py7zr.SevenZipFile(archive_path, mode='r') as archive:
            # Get list of files
            file_list = archive.getnames()
            bin_files = [f for f in file_list if f.lower().endswith('.bin')]
            
            if not bin_files:
                logging.error(f"No .bin file found in {archive_path}")
                return False
            if len(bin_files) > 1:
                logging.error(f"Multiple .bin files found in {archive_path}")
                return False
            
            # Extract all files (in case there are related files we might need)
            logging.info(f"Extracting {archive_path.name} to {subdir}")
            archive.extractall(subdir)
            
            # Verify the .bin file was extracted
            bin_path = subdir / bin_files[0]
            if not bin_path.exists():
                logging.error(f"Extraction appeared to succeed but .bin file not found: {bin_path}")
                return False
                
            size = bin_path.stat().st_size
            logging.info(f"Successfully extracted {bin_files[0]} ({size:,} bytes)")
            return True
            
    except Exception as e:
        logging.error(f"Failed to extract {archive_path}: {str(e)}")
        # Clean up failed extraction
        if subdir.exists():
            try:
                shutil.rmtree(subdir)
                logging.info(f"Cleaned up failed extraction directory: {subdir}")
            except Exception as cleanup_error:
                logging.error(f"Error cleaning up directory {subdir}: {cleanup_error}")
        return False

def process_archives(input_dir: Path, output_dir: Path):
    """Process all .7z files in the input directory"""
    archives = list(input_dir.glob('*.7z'))
    total_files = len(archives)
    
    if total_files == 0:
        logging.error(f"No .7z files found in {input_dir}")
        return
    
    logging.info(f"Found {total_files} archives to process")
    
    # Statistics
    successful = 0
    failed = 0
    interrupted = 0
    
    for index, archive_path in enumerate(archives, 1):
        if shutdown_requested:
            interrupted = total_files - (successful + failed)
            break
        
        logging.info(f"\nProcessing [{index}/{total_files}]: {archive_path.name}")
        
        if extract_archive(archive_path, output_dir):
            successful += 1
        else:
            failed += 1
        
        if index % 10 == 0:  # Log progress every 10 files
            logging.info(f"\nProgress Update:")
            logging.info(f"Processed: {index}/{total_files} files")
            logging.info(f"Success rate: {successful/(successful+failed)*100:.1f}%")
    
    # Log final statistics
    logging.info("\nExtraction Statistics:")
    logging.info(f"Total archives found: {total_files}")
    logging.info(f"Successfully extracted: {successful}")
    logging.info(f"Failed extractions: {failed}")
    if interrupted > 0:
        logging.info(f"Remaining archives (not processed due to shutdown): {interrupted}")

def main():
    parser = argparse.ArgumentParser(description='Extract .bin files from .7z archives')
    parser.add_argument('input_dir', help='Directory containing .7z files')
    parser.add_argument('output_dir', help='Directory for extracted files')
    args = parser.parse_args()
    
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    
    if not input_dir.is_dir():
        print(f"Error: {input_dir} is not a valid directory")
        sys.exit(1)
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(exist_ok=True)
    
    # Setup logging
    log_file = setup_logging(output_dir)
    
    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logging.info(f"Starting extraction process")
    logging.info(f"Input directory: {input_dir}")
    logging.info(f"Output directory: {output_dir}")
    logging.info(f"Log file: {log_file}")
    
    try:
        process_archives(input_dir, output_dir)
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        if shutdown_requested:
            logging.info("Shutdown complete. Partial extractions may need cleanup.")
        else:
            logging.info("Processing complete.")

if __name__ == "__main__":
    main()