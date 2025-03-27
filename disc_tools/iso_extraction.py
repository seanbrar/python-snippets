import py7zr
import os
import shutil
from pathlib import Path
import tempfile
import signal
import sys

# Global flag for graceful shutdown
shutdown_requested = False

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    global shutdown_requested
    print("\nShutdown requested. Completing current operation...")
    shutdown_requested = True

def process_7z_files(folder_path):
    """
    Process all .7z files in the given folder according to specified rules.
    Optimized for slow disk performance.
    """
    folder = Path(folder_path)
    archive_paths = list(folder.glob('*.7z'))
    
    with tempfile.TemporaryDirectory(dir=folder) as temp_base:
        temp_dir = Path(temp_base)
        
        for archive_path in archive_paths:
            if shutdown_requested:
                print("Shutting down gracefully...")
                break
                
            print(f"Processing: {archive_path}")
            
            try:
                with py7zr.SevenZipFile(archive_path, mode='r') as archive:
                    file_list = archive.getnames()
                    iso_files = [f for f in file_list if f.lower().endswith('.iso')]
                    
                    if not (len(iso_files) == 1 and len(file_list) == 1) and len(file_list) <= 1:
                        print(f"Skipping {archive_path} - doesn't match criteria")
                        continue
                    
                    # Single ISO case
                    if len(iso_files) == 1 and len(file_list) == 1:
                        # Clear temp directory but reuse it
                        for item in temp_dir.iterdir():
                            if not shutdown_requested:  # Check during cleanup
                                item.unlink()
                            else:
                                break
                        
                        if shutdown_requested:
                            break
                        
                        archive.extractall(temp_dir)
                        extracted_iso = temp_dir / iso_files[0]
                        
                        if extracted_iso.exists() and extracted_iso.stat().st_size > 0:
                            # Use archive name for the ISO file
                            target_path = archive_path.parent / f"{archive_path.stem}.iso"
                            
                            # Handle case where target already exists
                            if target_path.exists():
                                print(f"Warning: {target_path} already exists, appending number...")
                                counter = 1
                                while target_path.exists():
                                    target_path = archive_path.parent / f"{archive_path.stem}_{counter}.iso"
                                    counter += 1
                            
                            shutil.copy2(str(extracted_iso), str(target_path))
                            archive_path.unlink()
                            print(f"Successfully extracted to {target_path.name}")
                    
                    # Multiple files case
                    elif len(file_list) > 1:
                        subfolder = archive_path.parent / f"extracted_{archive_path.stem}"
                        subfolder.mkdir(exist_ok=True)
                        archive.extractall(subfolder)
                        print(f"Extracted to {subfolder}")
            
            except Exception as e:
                print(f"Error processing archive {archive_path}: {e}")
                if shutdown_requested:
                    break

def main():
    if len(sys.argv) != 2:
        print("Usage: python script.py <folder_path>")
        sys.exit(1)
    
    folder_path = sys.argv[1]
    if not os.path.isdir(folder_path):
        print(f"Error: {folder_path} is not a valid directory")
        sys.exit(1)
    
    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Termination request
    
    try:
        process_7z_files(folder_path)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        if shutdown_requested:
            print("Shutdown complete.")
        else:
            print("Processing complete.")

if __name__ == "__main__":
    main()