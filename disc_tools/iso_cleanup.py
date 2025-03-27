import os
import sys
import logging
from pathlib import Path
from datetime import datetime

def setup_logging():
    """Configure logging to both file and console"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = f'iso_cleanup_{timestamp}.log'
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return log_file

def cleanup_isos(folder_path: str, dry_run: bool = True):
    """Remove ISO files that have corresponding CHD files"""
    folder = Path(folder_path)
    iso_files = list(folder.glob('*.iso'))
    total_files = len(iso_files)
    
    if total_files == 0:
        logging.error(f"No ISO files found in {folder_path}")
        return
    
    logging.info(f"Found {total_files} ISO files to check")
    
    # Statistics
    would_delete = 0  # For dry run mode
    deleted = 0
    skipped = 0
    total_bytes = 0  # Track total size
    
    for iso_path in iso_files:
        chd_path = iso_path.with_suffix('.chd')
        
        if chd_path.exists() and chd_path.stat().st_size > 0:
            file_size = iso_path.stat().st_size
            total_bytes += file_size
            if dry_run:
                logging.info(f"Would delete: {iso_path.name} (matching CHD exists, size: {file_size/1e9:.2f} GB)")
                would_delete += 1
            else:
                try:
                    iso_path.unlink()
                    logging.info(f"Deleted: {iso_path.name}")
                    deleted += 1
                except Exception as e:
                    logging.error(f"Failed to delete {iso_path.name}: {str(e)}")
        else:
            logging.info(f"Keeping: {iso_path.name} (no valid CHD found)")
            skipped += 1
    
    # Log final statistics
    logging.info("\nCleanup Statistics:")
    if dry_run:
        logging.info(f"Would delete: {would_delete} files")
    else:
        logging.info(f"Deleted: {deleted} files")
    logging.info(f"Skipped: {skipped} files")
    logging.info(f"Total space that will be freed: {total_bytes/1e9:.2f} GB")

def main():
    if len(sys.argv) not in [2, 3]:
        print("Usage: python iso-cleanup.py <folder_path> [--execute]")
        print("  --execute: Actually delete files. Without this, runs in dry-run mode.")
        sys.exit(1)
    
    folder_path = sys.argv[1]
    if not os.path.isdir(folder_path):
        print(f"Error: {folder_path} is not a valid directory")
        sys.exit(1)
    
    dry_run = True
    if len(sys.argv) == 3 and sys.argv[2] == '--execute':
        dry_run = False
    
    # Setup logging
    log_file = setup_logging()
    
    logging.info(f"Starting ISO cleanup process. Log file: {log_file}")
    logging.info(f"Mode: {'Dry run' if dry_run else 'Execute'}")
    
    try:
        cleanup_isos(folder_path, dry_run)
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        logging.info("Processing complete.")

if __name__ == "__main__":
    main()