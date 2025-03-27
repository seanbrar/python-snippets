import subprocess
import os
import signal
import sys
from pathlib import Path
import logging
from datetime import datetime
import tempfile
import py7zr
import shutil

# Global flags for graceful shutdown and process tracking
shutdown_requested = False
current_process = None

def setup_logging():
    """Configure logging to both file and console"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = f'bin_conversion_{timestamp}.log'
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return log_file

def verify_chdman():
    """Verify that chdman utility is available and working"""
    try:
        logging.info("Testing chdman availability...")
        # Just run chdman without arguments - it will show usage and return 1
        result = subprocess.run(['chdman'], 
                              capture_output=True, 
                              text=True)
        
        # Check if the output contains expected chdman usage text
        if "MAME Compressed Hunks of Data (CHD) manager" in result.stdout:
            logging.info("chdman found and working")
            return True
            
        logging.error("chdman found but unexpected output")
        logging.info(f"chdman stdout: {result.stdout[:200]}...")
        return False
        
    except FileNotFoundError:
        logging.error("chdman not found in PATH")
        logging.info(f"Current PATH: {os.environ.get('PATH', 'Not set')}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error testing chdman: {str(e)}")
        return False

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

def extract_7z(archive_path: Path, temp_dir: Path) -> Path:
    """
    Extract .bin file from .7z archive
    Returns path to extracted .bin file or None if failed
    """
    try:
        with py7zr.SevenZipFile(archive_path, mode='r') as archive:
            # Get list of files
            file_list = archive.getnames()
            bin_files = [f for f in file_list if f.lower().endswith('.bin')]
            
            if not bin_files:
                logging.error(f"No .bin file found in {archive_path}")
                return None
            if len(bin_files) > 1:
                logging.error(f"Multiple .bin files found in {archive_path}")
                return None
            
            # Extract the single .bin file
            logging.info(f"Extracting {bin_files[0]}")
            archive.extract(temp_dir, targets=bin_files)
            
            if shutdown_requested:
                logging.info(f"Extraction interrupted for {archive_path}")
                return None
            
            extracted_path = temp_dir / bin_files[0]
            if not extracted_path.exists():
                logging.error(f"Extraction appeared to succeed but file not found: {extracted_path}")
                return None
                
            size = extracted_path.stat().st_size
            logging.info(f"Successfully extracted {bin_files[0]} ({size:,} bytes)")
            return extracted_path
            
    except Exception as e:
        logging.error(f"Failed to extract {archive_path}: {str(e)}")
        return None

def convert_to_chd(bin_path: Path, chd_path: Path, num_processors: int) -> bool:
    """Convert a .bin file to CHD format"""
    global current_process
    
    try:
        if not bin_path.exists():
            logging.error(f"BIN file not found: {bin_path}")
            return False
        
        logging.info(f"Starting conversion of {bin_path.name} ({bin_path.stat().st_size:,} bytes)")
        
        cmd = [
            'chdman', 'createcd',
            '-i', str(bin_path),
            '-o', str(chd_path),
            '-c', 'zstd,lzma,huff',
            '-np', str(num_processors),
            '-f'
        ]
        
        # Run process with a timeout, without trying to capture output
        process = subprocess.run(
            cmd,
            timeout=3600,  # 1 hour timeout
            check=True
        )
        
        # If we get here, the process completed successfully
        if chd_path.exists() and chd_path.stat().st_size > 1000:
            logging.info(f"Successfully converted {bin_path.name} to CHD ({chd_path.stat().st_size:,} bytes)")
            return True
        else:
            logging.error(f"Conversion failed - CHD file missing or too small")
            cleanup_incomplete_chd(chd_path)
            return False
            
    except subprocess.TimeoutExpired:
        logging.error(f"Conversion timed out after 1 hour for {bin_path.name}")
        cleanup_incomplete_chd(chd_path)
        return False
    except subprocess.CalledProcessError as e:
        logging.error(f"Conversion failed with return code {e.returncode}")
        cleanup_incomplete_chd(chd_path)
        return False
    except Exception as e:
        logging.error(f"Unexpected error converting {bin_path.name}: {str(e)}")
        cleanup_incomplete_chd(chd_path)
        return False

def process_archives(folder_path: str, num_processors: int = 16):
    """Process all .7z files in the given folder"""
    folder = Path(folder_path)
    archives = list(folder.glob('*.7z'))
    total_files = len(archives)
    
    if total_files == 0:
        logging.error(f"No .7z files found in {folder_path}")
        return
    
    logging.info(f"Found {total_files} archives to process")
    logging.info(f"Using {num_processors} processors for conversion")
    
    # Statistics
    successful = 0
    failed = 0
    skipped = 0
    interrupted = 0
    
    # Create temporary directory for extractions
    with tempfile.TemporaryDirectory(dir=folder) as temp_base:
        temp_dir = Path(temp_base)
        
        for index, archive_path in enumerate(archives, 1):
            if shutdown_requested:
                interrupted = total_files - (successful + failed + skipped)
                break
            
            logging.info(f"\nProcessing [{index}/{total_files}]: {archive_path.name}")
            
            # Check if CHD already exists
            chd_path = archive_path.with_suffix('.chd')
            if chd_path.exists():
                logging.info(f"CHD file already exists for {archive_path.name}, skipping...")
                skipped += 1
                continue
            
            # Clear temp directory but keep using it
            try:
                for item in temp_dir.iterdir():
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
            except Exception as e:
                logging.error(f"Error cleaning temporary directory: {e}")
                continue
            
            # Extract .bin file
            bin_path = extract_7z(archive_path, temp_dir)
            if not bin_path:
                if shutdown_requested:
                    interrupted = total_files - (successful + failed + skipped)
                    break
                failed += 1
                continue
            
            # Convert to CHD
            if convert_to_chd(bin_path, chd_path, num_processors):
                successful += 1
            else:
                if shutdown_requested:
                    interrupted = total_files - (successful + failed + skipped)
                    break
                failed += 1
            
            # Log progress periodically
            if index % 5 == 0:  # Changed from 10 to 5 for more frequent updates
                logging.info(f"\nProgress Update:")
                logging.info(f"Processed: {index}/{total_files} files")
                if successful + failed > 0:
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
        print("Usage: python bin_to_chd.py <folder_path>")
        sys.exit(1)
    
    folder_path = sys.argv[1]
    if not os.path.isdir(folder_path):
        print(f"Error: {folder_path} is not a valid directory")
        sys.exit(1)
    
    # Setup logging
    log_file = setup_logging()
    
    # Verify chdman is available
    if not verify_chdman():
        logging.error("Required chdman utility not found or not working")
        sys.exit(1)
    
    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logging.info(f"Starting conversion process. Log file: {log_file}")
    
    try:
        process_archives(folder_path, num_processors=16)
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