import subprocess
import os
import signal
import sys
from pathlib import Path
import logging
from datetime import datetime
import threading

# Global flags for graceful shutdown
shutdown_requested = False
current_process = None

def setup_logging():
    """Configure logging to both file and console"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = f'chd_conversion_{timestamp}.log'
    
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
    
    # If there's an active conversion process, terminate it
    if current_process:
        try:
            # Send SIGTERM to the process group
            os.killpg(os.getpgid(current_process.pid), signal.SIGTERM)
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

def convert_to_chd(iso_path: Path, output_path: Path, num_processors: int) -> bool:
    """
    Convert a single ISO to CHD format using chdman
    Returns True if successful, False otherwise
    """
    global current_process
    
    try:
        cmd = [
            'chdman', 'createcd',
            '-i', str(iso_path),
            '-o', str(output_path),
            '-c', 'zstd,lzma,huff',
            '-np', str(num_processors),
            '-f'
        ]
        
        # Start process in a new process group
        current_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=os.setsid  # Create new process group
        )
        
        # Monitor the process
        stdout, stderr = current_process.communicate()
        
        if shutdown_requested:
            logging.info(f"Conversion of {iso_path.name} interrupted by shutdown request")
            cleanup_incomplete_chd(output_path)
            return False
            
        if current_process.returncode == 0:
            logging.info(f"Successfully converted {iso_path.name}")
            return True
        else:
            logging.error(f"Error converting {iso_path.name}: {stderr}")
            cleanup_incomplete_chd(output_path)
            return False
            
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to convert {iso_path.name}: {e.stderr}")
        cleanup_incomplete_chd(output_path)
        return False
    except Exception as e:
        logging.error(f"Unexpected error converting {iso_path.name}: {str(e)}")
        cleanup_incomplete_chd(output_path)
        return False
    finally:
        current_process = None

def process_isos(folder_path: str, num_processors: int = 16):
    """Process all ISO files in the given folder"""
    folder = Path(folder_path)
    iso_files = list(folder.glob('*.iso'))
    total_files = len(iso_files)
    
    if total_files == 0:
        logging.error(f"No ISO files found in {folder_path}")
        return
    
    logging.info(f"Found {total_files} ISO files to process")
    logging.info(f"Using {num_processors} processors for conversion")
    
    # Statistics
    successful = 0
    failed = 0
    skipped = 0
    interrupted = 0
    
    for index, iso_path in enumerate(iso_files, 1):
        if shutdown_requested:
            interrupted = total_files - (successful + failed + skipped)
            break
        
        logging.info(f"Processing [{index}/{total_files}]: {iso_path.name}")
        
        chd_path = iso_path.with_suffix('.chd')
        if chd_path.exists():
            logging.info(f"CHD file already exists for {iso_path.name}, skipping...")
            skipped += 1
            continue
        
        if convert_to_chd(iso_path, chd_path, num_processors):
            successful += 1
        else:
            if shutdown_requested:
                interrupted = total_files - (successful + failed + skipped)
                break
            failed += 1
        
        if index % 10 == 0:  # Log progress every 10 files
            logging.info(f"\nProgress Update:")
            logging.info(f"Processed: {index}/{total_files} files")
            logging.info(f"Success rate: {successful/(successful+failed)*100:.1f}%")
    
    # Log final statistics
    logging.info("\nConversion Statistics:")
    logging.info(f"Total files found: {total_files}")
    logging.info(f"Successfully converted: {successful}")
    logging.info(f"Failed conversions: {failed}")
    logging.info(f"Skipped (already exist): {skipped}")
    if interrupted > 0:
        logging.info(f"Remaining files (not processed due to shutdown): {interrupted}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python chd-creator.py <folder_path>")
        sys.exit(1)
    
    folder_path = sys.argv[1]
    if not os.path.isdir(folder_path):
        print(f"Error: {folder_path} is not a valid directory")
        sys.exit(1)
    
    # Setup logging
    log_file = setup_logging()
    
    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logging.info(f"Starting CHD conversion process. Log file: {log_file}")
    
    try:
        process_isos(folder_path, num_processors=16)
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