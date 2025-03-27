#!/usr/bin/env python3
import argparse
import logging
import signal
import sys
import subprocess
from datetime import datetime
from pathlib import Path

# Global flags
shutdown_requested = False
current_process = None

def setup_logging(base_dir: Path) -> Path:
    """Configure logging to both file and console"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = base_dir / f'chdcreate_{timestamp}.log'
    
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
    global shutdown_requested, current_process
    logging.info("\nShutdown requested. Completing current operation...")
    shutdown_requested = True
    
    if current_process:
        try:
            current_process.terminate()
        except Exception as e:
            logging.error(f"Error terminating conversion process: {e}")

def cleanup_incomplete_chd(chd_path: Path):
    """Remove incomplete CHD file if it exists"""
    try:
        if chd_path.exists():
            chd_path.unlink()
            logging.info(f"Cleaned up incomplete CHD file: {chd_path}")
    except Exception as e:
        logging.error(f"Error cleaning up incomplete CHD file {chd_path}: {e}")

def create_chd(cue_path: Path, chd_path: Path, num_processors: int) -> bool:
    """Convert files to CHD format"""
    global current_process
    
    try:
        logging.info(f"Starting conversion: {cue_path.parent.name}")
        
        cmd = [
            'chdman', 'createcd',
            '-i', str(cue_path),
            '-o', str(chd_path),
            '-c', 'zstd,lzma,huff',
            '-np', str(num_processors)
        ]
        
        # Run the conversion process
        current_process = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )
        
        if chd_path.exists() and chd_path.stat().st_size > 1000:
            logging.info(f"Successfully created CHD: {chd_path.name} ({chd_path.stat().st_size:,} bytes)")
            return True
        else:
            logging.error("CHD file missing or too small")
            cleanup_incomplete_chd(chd_path)
            return False
            
    except subprocess.CalledProcessError as e:
        logging.error(f"Conversion failed: {e.stderr}")
        cleanup_incomplete_chd(chd_path)
        return False
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        cleanup_incomplete_chd(chd_path)
        return False
    finally:
        current_process = None

def process_directories(base_dir: Path, output_dir: Path, num_processors: int):
    """Process all game directories"""
    game_dirs = [d for d in base_dir.iterdir() if d.is_dir()]
    total_dirs = len(game_dirs)
    
    if total_dirs == 0:
        logging.error(f"No subdirectories found in {base_dir}")
        return
    
    logging.info(f"Found {total_dirs} directories to process")
    logging.info(f"Using {num_processors} processors for conversion")
    
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
        
        # Output CHD path based on directory name
        chd_path = output_dir / f"{game_dir.name}.chd"
        
        if chd_path.exists():
            logging.info(f"CHD file already exists, skipping: {chd_path}")
            skipped += 1
            continue
        
        # Find .cue file in the directory
        cue_files = list(game_dir.glob('*.cue'))
        
        if not cue_files:
            logging.error(f"No .cue file found in {game_dir}")
            failed += 1
            continue
        if len(cue_files) > 1:
            logging.error(f"Multiple .cue files found in {game_dir}")
            failed += 1
            continue
        
        # Create CHD
        if create_chd(cue_files[0], chd_path, num_processors):
            successful += 1
        else:
            failed += 1
        
        if index % 5 == 0:  # Log progress every 5 directories
            logging.info(f"\nProgress Update:")
            logging.info(f"Processed: {index}/{total_dirs} directories")
            if successful + failed > 0:
                logging.info(f"Success rate: {successful/(successful+failed)*100:.1f}%")
    
    # Log final statistics
    logging.info("\nCHD Creation Statistics:")
    logging.info(f"Total directories found: {total_dirs}")
    logging.info(f"Successfully converted: {successful}")
    logging.info(f"Failed conversions: {failed}")
    logging.info(f"Skipped (already exist): {skipped}")
    if interrupted > 0:
        logging.info(f"Remaining directories (not processed due to shutdown): {interrupted}")

def main():
    parser = argparse.ArgumentParser(description='Create CHD files from extracted games')
    parser.add_argument('base_dir', help='Base directory containing game subdirectories')
    parser.add_argument('output_dir', help='Output directory for CHD files')
    parser.add_argument('--processors', '-np', type=int, default=16,
                       help='Number of processors to use (default: 16)')
    args = parser.parse_args()
    
    base_dir = Path(args.base_dir)
    output_dir = Path(args.output_dir)
    
    if not base_dir.is_dir():
        print(f"Error: {base_dir} is not a valid directory")
        sys.exit(1)
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(exist_ok=True)
    
    # Setup logging
    log_file = setup_logging(output_dir)
    
    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logging.info(f"Starting CHD creation process")
    logging.info(f"Base directory: {base_dir}")
    logging.info(f"Output directory: {output_dir}")
    logging.info(f"Log file: {log_file}")
    
    try:
        process_directories(base_dir, output_dir, args.processors)
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        if shutdown_requested:
            logging.info("Shutdown complete. Any incomplete conversions were cleaned up.")
        else:
            logging.info("Processing complete.")

if __name__ == "__main__":
    main()