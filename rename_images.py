#!/usr/bin/env python
"""
Script untuk rename image files di filesystem agar match dengan database

MASALAH:
- Database: "Dr. STONE: STONE WARS.jpg" 
- Filesystem: TIDAK BISA buat file dengan titik dua (:)
- Solution: Rename file jadi "Dr. STONE STONE WARS.jpg" (hapus titik dua)

Usage:
    python rename_images.py

atau

    python rename_images.py /path/to/images/cover /path/to/images/wallpaper
"""

import os
import sys
from pathlib import Path
import re


def sanitize_filename(filename):
    """
    Sanitize filename - HARUS SAMA dengan fungsi di views.py!
    """
    if not filename:
        return "default.jpg"
    
    # HAPUS titik dua dan karakter illegal
    safe = filename.replace(':', '')  # PENTING!
    safe = safe.replace('/', '')
    safe = safe.replace('\\', '')
    safe = safe.replace('<', '')
    safe = safe.replace('>', '')
    safe = safe.replace('"', '')
    safe = safe.replace('|', '')
    safe = safe.replace('?', '')
    safe = safe.replace('*', '')
    
    # Clean up spaces
    safe = re.sub(r'\s+', ' ', safe).strip()
    
    if not safe or safe in ('.jpg', '.png'):
        return "default.jpg"
    
    return safe


def rename_images_in_directory(directory, dry_run=True):
    """
    Rename semua images di directory untuk match dengan sanitized names
    
    Args:
        directory (str): Path ke directory
        dry_run (bool): Jika True, hanya print tanpa rename
    """
    dir_path = Path(directory)
    
    if not dir_path.exists():
        print(f"❌ Directory tidak ditemukan: {directory}")
        return
    
    print("=" * 80)
    print(f"RENAME IMAGES - {'DRY RUN (preview only)' if dry_run else 'LIVE MODE'}")
    print("=" * 80)
    print(f"Directory: {directory}")
    print()
    
    # Get all image files
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.webp', '*.gif', '*.JPG', '*.PNG']
    all_files = []
    for ext in image_extensions:
        all_files.extend(dir_path.glob(ext))
    
    if not all_files:
        print("⚠️  Tidak ada file gambar di directory ini")
        return
    
    print(f"Total files: {len(all_files)}")
    print()
    
    renamed_count = 0
    skipped_count = 0
    error_count = 0
    
    for file_path in sorted(all_files):
        original_name = file_path.name
        safe_name = sanitize_filename(original_name)
        
        # Skip jika sudah safe
        if original_name == safe_name:
            skipped_count += 1
            continue
        
        new_path = file_path.parent / safe_name
        
        print(f"📝 Rename:")
        print(f"   FROM: {original_name}")
        print(f"   TO:   {safe_name}")
        
        if not dry_run:
            try:
                # Check if target already exists
                if new_path.exists():
                    print(f"   ⚠️  WARNING: Target file already exists, skipping")
                    error_count += 1
                else:
                    file_path.rename(new_path)
                    print(f"   ✅ SUCCESS")
                    renamed_count += 1
            except Exception as e:
                print(f"   ❌ ERROR: {e}")
                error_count += 1
        else:
            print(f"   ℹ️  DRY RUN (tidak di-rename)")
            renamed_count += 1
        
        print()
    
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Files to rename: {renamed_count}")
    print(f"Files skipped (already safe): {skipped_count}")
    print(f"Errors: {error_count}")
    print(f"Total files: {len(all_files)}")
    
    if dry_run and renamed_count > 0:
        print()
        print("⚠️  Ini adalah DRY RUN - tidak ada file yang di-rename")
        print("   Untuk actual rename, jalankan dengan: python rename_images.py --live")


def main():
    """Main function"""
    
    # Parse arguments
    if len(sys.argv) > 1 and sys.argv[1] == '--live':
        dry_run = False
        print("\n🚨 LIVE MODE - Files akan di-rename!\n")
        
        response = input("Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("❌ Aborted")
            return
        
        start_idx = 2
    else:
        dry_run = True
        start_idx = 1
    
    # Get directories
    if len(sys.argv) > start_idx:
        directories = sys.argv[start_idx:]
    else:
        # Default directories
        base_dir = Path(__file__).parent
        directories = [
            base_dir / 'static' / 'images' / 'cover',
            base_dir / 'static' / 'images' / 'wallpaper',
        ]
        
        # Filter hanya yang exists
        directories = [str(d) for d in directories if d.exists()]
        
        if not directories:
            print("❌ Default directories tidak ditemukan")
            print("\nUsage:")
            print("  python rename_images.py [--live] [directory1] [directory2] ...")
            print("\nExamples:")
            print("  python rename_images.py  # Dry run default dirs")
            print("  python rename_images.py --live  # Live rename default dirs")
            print("  python rename_images.py /path/to/cover  # Dry run custom dir")
            print("  python rename_images.py --live /path/to/cover  # Live custom dir")
            return
    
    # Process each directory
    for directory in directories:
        rename_images_in_directory(directory, dry_run=dry_run)
        print()


if __name__ == '__main__':
    main()