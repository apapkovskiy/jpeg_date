#!/usr/bin/env python3
"""
JPEG Date Modifier Script

This script modifies the date in JPEG images by changing only the year and month,
while keeping the day unchanged. It updates both EXIF metadata and file modification date.
Supports processing single files or entire folders (with optional recursive processing).

Requirements:
    pip install pillow piexif

Usage:
    # Single file - change year and month
    python jpeg_date.py photo.jpg 2023 12
    
    # Single file - change only year (keep original month)
    python jpeg_date.py photo.jpg 2023
    
    # Folder (all JPEG files in folder)
    python jpeg_date.py /path/to/photos 2023 12
    
    # Folder with recursive processing
    python jpeg_date.py /path/to/photos 2023 12 --recursive
    
    # Dry run (see what would be changed)
    python jpeg_date.py /path/to/photos 2023 12 --dry-run
    
    # Show current dates without changing
    python jpeg_date.py /path/to/photos 2023 12 --show-current
    
Examples:
    python jpeg_date.py photo.jpg 2023 12        # Change year and month
    python jpeg_date.py photo.jpg 2023           # Change only year
    python jpeg_date.py ./photos 2010 7 -r -o ./modified_photos
    python jpeg_date.py ./vacation_pics 2023 --dry-run --recursive
"""

import os
import sys
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS
import argparse


def get_image_datetime(image_path):
    """Extract datetime from JPEG EXIF data."""
    try:
        with Image.open(image_path) as image:
            exif_data = image.getexif()
            
            if exif_data is not None:
                for tag, value in exif_data.items():
                    tag_name = TAGS.get(tag, tag)
                    if tag_name == "DateTime":
                        return datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
            
            print("No DateTime found in EXIF data")
            return None
    except (OSError, ValueError, KeyError) as e:
        print(f"Error reading image datetime: {e}")
        return None


def modify_image_datetime(image_path, new_year, new_month=None, output_path=None):
    """
    Modify the datetime in JPEG EXIF data and file modification time.
    
    Args:
        image_path (str): Path to the input JPEG image
        new_year (int): New year to set
        new_month (int): New month to set (1-12). If None, keeps original month
        output_path (str): Optional output path. If None, overwrites original file
    """
    try:
        # Read the original image
        with Image.open(image_path) as image:
            # Get current datetime from EXIF
            current_datetime = get_image_datetime(image_path)
            
            if current_datetime is None:
                # If no datetime in EXIF, use file modification time
                file_time = os.path.getmtime(image_path)
                current_datetime = datetime.fromtimestamp(file_time)
                print(f"Using file modification time: {current_datetime}")
            
            # Create new datetime with modified year and optionally month, keeping original day and time
            if new_month is not None:
                new_datetime = current_datetime.replace(year=new_year, month=new_month)
            else:
                new_datetime = current_datetime.replace(year=new_year)
            
            print(f"Original datetime: {current_datetime}")
            print(f"New datetime: {new_datetime}")
            
            # Save the image first
            if output_path is None:
                output_path = image_path
            
            # Save image
            if image.format == 'JPEG':
                image.save(output_path, format='JPEG', quality=95)
                
                # For more reliable EXIF editing, we'll use piexif
                update_exif_with_piexif(output_path, new_datetime)
            else:
                print(f"Warning: File format is {image.format}, not JPEG")
                
    except (OSError, ValueError) as e:
        print(f"Error modifying image datetime: {e}")
        return False
    
    # Update file modification time
    try:
        new_timestamp = new_datetime.timestamp()
        os.utime(output_path, (new_timestamp, new_timestamp))
        print(f"Updated file modification time to: {new_datetime}")
    except OSError as e:
        print(f"Error updating file modification time: {e}")
    
    return True


def update_exif_with_piexif(image_path, new_datetime):
    """Update EXIF using piexif library for more reliable results."""
    try:
        import piexif
        
        exif_dict = piexif.load(image_path)
        datetime_str = new_datetime.strftime("%Y:%m:%d %H:%M:%S")
        
        # Update datetime fields
        exif_dict['0th'][piexif.ImageIFD.DateTime] = datetime_str
        exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = datetime_str
        exif_dict['Exif'][piexif.ExifIFD.DateTimeDigitized] = datetime_str
        
        # Convert back to bytes and save
        exif_bytes = piexif.dump(exif_dict)
        piexif.insert(exif_bytes, image_path)
        
        print("EXIF data updated successfully using piexif")
        
    except ImportError:
        print("piexif not installed. Install with: pip install piexif")
        print("Using basic PIL EXIF handling (may be less reliable)")
    except (ValueError, KeyError, OSError) as e:
        print(f"Error with piexif: {e}")


def is_jpeg_file(file_path):
    """Check if a file is a JPEG image based on extension."""
    jpeg_extensions = {'.jpg', '.jpeg', '.JPG', '.JPEG'}
    return os.path.splitext(file_path)[1] in jpeg_extensions


def find_jpeg_files(folder_path, recursive=False):
    """Find all JPEG files in a folder."""
    jpeg_files = []
    
    if recursive:
        # Search recursively in subdirectories
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                if is_jpeg_file(file_path):
                    jpeg_files.append(file_path)
    else:
        # Search only in the specified folder
        for file in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file)
            if os.path.isfile(file_path) and is_jpeg_file(file_path):
                jpeg_files.append(file_path)
    
    return sorted(jpeg_files)


def process_folder(folder_path, new_year, new_month=None, output_folder=None, recursive=False, dry_run=False):
    """
    Process all JPEG files in a folder.
    
    Args:
        folder_path (str): Path to the folder containing JPEG images
        new_year (int): New year to set
        new_month (int): New month to set (1-12). If None, keeps original month
        output_folder (str): Optional output folder. If None, overwrites original files
        recursive (bool): Process subdirectories recursively
        dry_run (bool): Show what would be processed without making changes
    
    Returns:
        tuple: (success_count, error_count, total_files)
    """
    jpeg_files = find_jpeg_files(folder_path, recursive)
    
    if not jpeg_files:
        print(f"No JPEG files found in {'(recursively)' if recursive else ''} {folder_path}")
        return 0, 0, 0
    
    print(f"Found {len(jpeg_files)} JPEG files in {folder_path}")
    if recursive:
        print("Processing recursively...")
    
    if dry_run:
        print("\n--- DRY RUN MODE (no changes will be made) ---")
        for i, file_path in enumerate(jpeg_files, 1):
            print(f"{i:3d}. {os.path.basename(file_path)}")
            current_dt = get_image_datetime(file_path)
            if current_dt:
                if new_month is not None:
                    new_dt = current_dt.replace(year=new_year, month=new_month)
                else:
                    new_dt = current_dt.replace(year=new_year)
                print(f"     {current_dt} -> {new_dt}")
            else:
                print("     No EXIF datetime found")
        print(f"\nWould process {len(jpeg_files)} files.")
        return 0, 0, len(jpeg_files)
    
    success_count = 0
    error_count = 0
    
    for i, file_path in enumerate(jpeg_files, 1):
        print(f"\n[{i}/{len(jpeg_files)}] Processing: {os.path.basename(file_path)}")
        
        try:
            # Determine output path
            if output_folder:
                # Create output folder if it doesn't exist
                os.makedirs(output_folder, exist_ok=True)
                
                # Preserve folder structure if processing recursively
                if recursive:
                    # Get relative path from original folder
                    rel_path = os.path.relpath(file_path, folder_path)
                    output_path = os.path.join(output_folder, rel_path)
                    # Create subdirectories in output folder if needed
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                else:
                    output_path = os.path.join(output_folder, os.path.basename(file_path))
            else:
                output_path = None  # Overwrite original
            
            # Process the file
            success = modify_image_datetime(file_path, new_year, new_month, output_path)
            
            if success:
                success_count += 1
                print("✓ Successfully processed")
            else:
                error_count += 1
                print("✗ Failed to process")
                
        except (OSError, ValueError) as e:
            error_count += 1
            print(f"✗ Error processing {file_path}: {e}")
    
    print("\n--- Summary ---")
    print(f"Total files: {len(jpeg_files)}")
    print(f"Successfully processed: {success_count}")
    print(f"Errors: {error_count}")
    
    return success_count, error_count, len(jpeg_files)


def main():
    parser = argparse.ArgumentParser(
        description="Modify JPEG image date (year and month only, keeping day unchanged)"
    )
    parser.add_argument("path", help="Path to JPEG image or folder containing JPEG images")
    parser.add_argument("new_year", type=int, help="New year (e.g., 2023)")
    parser.add_argument("new_month", type=int, nargs='?', default=None, help="New month (1-12, optional - keeps original month if not specified)")
    parser.add_argument("-o", "--output", help="Output path/folder (optional, overwrites original if not specified)")
    parser.add_argument("--show-current", "-s", action="store_true", help="Show current datetime and exit")
    parser.add_argument("--recursive", "-r", action="store_true", help="Process folders recursively")
    parser.add_argument("--dry-run", "-d", action="store_true", help="Show what would be processed without making changes")
    
    args = parser.parse_args()
    
    # Validate inputs
    if not os.path.exists(args.path):
        print(f"Error: Path '{args.path}' not found")
        sys.exit(1)
    
    if args.new_month is not None and not (1 <= args.new_month <= 12):
        print("Error: Month must be between 1 and 12")
        sys.exit(1)
    
    if args.new_year < 1900 or args.new_year > 2100:
        print("Error: Year seems unrealistic")
        sys.exit(1)
    
    # Check if path is a file or folder
    is_folder = os.path.isdir(args.path)
    
    if args.show_current:
        if is_folder:
            # Show current datetime for all JPEG files in folder
            jpeg_files = find_jpeg_files(args.path, args.recursive)
            if not jpeg_files:
                print(f"No JPEG files found in {args.path}")
                sys.exit(1)
            
            print(f"Found {len(jpeg_files)} JPEG files:")
            for file_path in jpeg_files:
                current_dt = get_image_datetime(file_path)
                if current_dt:
                    print(f"{os.path.basename(file_path)}: {current_dt}")
                else:
                    file_time = os.path.getmtime(file_path)
                    current_dt = datetime.fromtimestamp(file_time)
                    print(f"{os.path.basename(file_path)}: {current_dt} (file time)")
        else:
            # Show current datetime for single file
            if not is_jpeg_file(args.path):
                print(f"Error: '{args.path}' is not a JPEG file")
                sys.exit(1)
            
            current_dt = get_image_datetime(args.path)
            if current_dt:
                print(f"Current image datetime: {current_dt}")
            else:
                file_time = os.path.getmtime(args.path)
                current_dt = datetime.fromtimestamp(file_time)
                print(f"Current file modification time: {current_dt}")
        
        sys.exit(0)
    
    # Process file or folder
    if is_folder:
        # Process folder
        success_count, error_count, total_files = process_folder(
            args.path, 
            args.new_year, 
            args.new_month, 
            args.output, 
            args.recursive,
            args.dry_run
        )
        
        if args.dry_run:
            sys.exit(0)
        
        if error_count > 0:
            print(f"\nCompleted with {error_count} errors out of {total_files} files")
            sys.exit(1)
        else:
            print(f"\nAll {success_count} files processed successfully!")
    else:
        # Process single file
        if not is_jpeg_file(args.path):
            print(f"Error: '{args.path}' is not a JPEG file")
            sys.exit(1)
        
        if args.dry_run:
            print("--- DRY RUN MODE (no changes will be made) ---")
            current_dt = get_image_datetime(args.path)
            if current_dt:
                if args.new_month is not None:
                    new_dt = current_dt.replace(year=args.new_year, month=args.new_month)
                else:
                    new_dt = current_dt.replace(year=args.new_year)
                print(f"Would change: {current_dt} -> {new_dt}")
            else:
                print("No EXIF datetime found")
            sys.exit(0)
        
        success = modify_image_datetime(args.path, args.new_year, args.new_month, args.output)
        
        if success:
            print("Image datetime modified successfully!")
        else:
            print("Failed to modify image datetime")
            sys.exit(1)


if __name__ == "__main__":
    main()
