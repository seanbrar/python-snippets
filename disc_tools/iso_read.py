import sys
import os
import struct

# Constants
BYTES_TO_READ = 2048
SECTOR_SIZE = 4
REGION_SIZE = 8

# Simple logging functions
def log_info(message: str) -> None:
    print(f"[INFO] {message}")

def log_error(message: str) -> None:
    print(f"[ERROR] {message}", file=sys.stderr)

def read_iso_header(file_path: str, bytes_to_read: int = BYTES_TO_READ) -> bytes:
    """
    Reads the header of an ISO file.

    Args:
        file_path (str): Path to the ISO file.
        bytes_to_read (int, optional): Number of bytes to read from the header. Defaults to BYTES_TO_READ.

    Returns:
        bytes: The header data of the ISO file.

    Raises:
        FileNotFoundError: If the file does not exist.
        PermissionError: If the file cannot be accessed.
        Exception: For any other unforeseen errors.
    """
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"The file '{file_path}' does not exist.")

        with open(file_path, 'rb') as iso_file:
            header_data = iso_file.read(bytes_to_read)
            if len(header_data) < bytes_to_read:
                log_error(f"Expected {bytes_to_read} bytes, but only read {len(header_data)} bytes.")
                sys.exit(1)

        log_info("ISO header successfully read.")
        return header_data

    except FileNotFoundError as fnf_error:
        log_error(str(fnf_error))
        sys.exit(2)
    except PermissionError as perm_error:
        log_error(f"Permission denied: {perm_error}")
        sys.exit(3)
    except Exception as e:
        log_error(f"An unexpected error occurred: {str(e)}")
        sys.exit(1)

def parse_sector0(header_data: bytes) -> list:
    """
    Parses the first sector of the ISO header to extract unencrypted regions.

    Args:
        header_data (bytes): The header data from the ISO file.

    Returns:
        list: A list of tuples representing unencrypted regions (start_sector, end_sector).
    """
    if len(header_data) < SECTOR_SIZE:
        log_error("Insufficient data to read the number of unencrypted regions.")
        return []

    number_of_regions = struct.unpack('>I', header_data[:SECTOR_SIZE])[0]
    log_info(f"Number of Unencrypted Regions: {number_of_regions}")

    if number_of_regions * REGION_SIZE + SECTOR_SIZE > len(header_data):
        log_error("Header data is too short for the specified number of regions.")
        return []

    regions = []
    offset = SECTOR_SIZE
    for region_index in range(number_of_regions):
        if offset + REGION_SIZE > len(header_data):
            log_error(f"Unexpected end of data while reading region {region_index + 1}.")
            break
        start_sector, end_sector = struct.unpack('>II', header_data[offset:offset + REGION_SIZE])
        regions.append((start_sector, end_sector))
        log_info(f"Region {region_index + 1}: Start Sector = {start_sector}, End Sector = {end_sector}")
        offset += REGION_SIZE

    return regions

def display_hex(header_data: bytes, bytes_per_line: int = 16) -> None:
    """
    Displays a hex dump of the header data.

    Args:
        header_data (bytes): The header data to display.
        bytes_per_line (int, optional): Number of bytes per line in the dump. Defaults to 16.
    """
    log_info("\nHex Dump of Sector 0:")
    for i in range(0, len(header_data), bytes_per_line):
        line = header_data[i:i + bytes_per_line]
        hex_values = ' '.join(f"{byte:02X}" for byte in line)
        ascii_representation = ''.join((chr(byte) if 32 <= byte <= 126 else '.') for byte in line)
        print(f"{i:04X}: {hex_values:<{bytes_per_line * 3}} | {ascii_representation}")

def main() -> None:
    """
    The main function that orchestrates reading and parsing the ISO header.
    """
    if len(sys.argv) != 2:
        script_name = os.path.basename(sys.argv[0])
        log_error(f"Usage: python {script_name} <path_to_iso_file>")
        sys.exit(1)

    iso_path = sys.argv[1]
    log_info(f"Reading ISO header from: {iso_path}")
    
    header_data = read_iso_header(iso_path)
    regions = parse_sector0(header_data)
    
    if regions:
        log_info("Successfully parsed unencrypted regions.")
    else:
        log_info("No unencrypted regions found or failed to parse regions.")
    
    display_hex(header_data)

if __name__ == "__main__":
    main()
