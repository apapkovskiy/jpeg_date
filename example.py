#!/usr/bin/env python3
"""
Example usage of the JPEG date modifier script.
"""

from jpeg_date import modify_image_datetime, get_image_datetime, process_folder, find_jpeg_files
import os

def example_single_file():
    """Example of processing a single file."""
    image_path = "example.jpg"  # Replace with your image path
    
    if os.path.exists(image_path):
        # Show current date
        current_date = get_image_datetime(image_path)
        if current_date:
            print(f"Current date: {current_date}")
            
            # Change to year 2023, month 12, keeping the day and time
            success = modify_image_datetime(image_path, 2023, 12)
            if success:
                print("Date modified successfully!")
                
                # Show new date
                new_date = get_image_datetime(image_path)
                if new_date:
                    print(f"New date: {new_date}")
            else:
                print("Failed to modify date")
        else:
            print("Could not read current date from image")
    else:
        print(f"Image file {image_path} not found")

def example_folder():
    """Example of processing a folder."""
    folder_path = "./photos"  # Replace with your folder path
    
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        # Find JPEG files in folder
        jpeg_files = find_jpeg_files(folder_path, recursive=False)
        print(f"Found {len(jpeg_files)} JPEG files in {folder_path}")
        
        # Show what would be processed (dry run)
        print("\n--- Dry run to see what would be changed ---")
        process_folder(folder_path, 2023, 12, dry_run=True)
        
        # Actual processing (uncomment to actually modify files)
        # print("\n--- Processing files ---")
        # success_count, error_count, total_files = process_folder(
        #     folder_path, 2023, 12, output_folder="./modified_photos"
        # )
        
    else:
        print(f"Folder {folder_path} not found")

def main():
    """Main example function showing different usage patterns."""
    print("=== JPEG Date Modifier Examples ===\n")
    
    print("1. Single file processing:")
    example_single_file()
    
    print("\n" + "="*50 + "\n")
    
    print("2. Folder processing:")
    example_folder()
    
    print("\n" + "="*50 + "\n")
    
    print("Command line usage examples:")
    print("# Process single file:")
    print("python jpeg_date.py photo.jpg 2023 12")
    print()
    print("# Process all JPEG files in a folder:")
    print("python jpeg_date.py ./photos 2023 12")
    print()
    print("# Process folder recursively:")
    print("python jpeg_date.py ./photos 2023 12 --recursive")
    print()
    print("# Dry run (see what would be changed):")
    print("python jpeg_date.py ./photos 2023 12 --dry-run")
    print()
    print("# Save to different folder:")
    print("python jpeg_date.py ./photos 2023 12 -o ./modified_photos")
    print()
    print("# Show current dates without changing:")
    print("python jpeg_date.py ./photos 2023 12 --show-current")

if __name__ == "__main__":
    main()
