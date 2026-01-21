#!/usr/bin/env python
"""
Diagnostic script untuk check image paths dan sanitization

Usage: python manage.py shell < check_image_paths.py
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from main.models import Anime
from pathlib import Path

print("=" * 80)
print("IMAGE PATH DIAGNOSTIC")
print("=" * 80)

# Check Fate/Grand Order
fate = Anime.objects.filter(title__icontains='Fate/Grand Order').first()

if not fate:
    print("\n❌ Fate/Grand Order not found in database!")
else:
    print(f"\n✅ Found: {fate.title}")
    print(f"\n📊 Database Values:")
    print(f"   - Cover: {fate.cover}")
    print(f"   - Wallpaper: {fate.wallpaper}")
    print(f"   - Total Rating: {fate.total_rating}")
    
    # Sanitize function (MUST match views.py!)
    def sanitize_filename(filename):
        if not filename:
            return "default.jpg"
        import re
        safe = filename.replace(':', '')
        safe = safe.replace('/', '')
        safe = safe.replace('\\', '')
        safe = safe.replace('<', '')
        safe = safe.replace('>', '')
        safe = safe.replace('"', '')
        safe = safe.replace('|', '')
        safe = safe.replace('?', '')
        safe = safe.replace('*', '')
        safe = re.sub(r'\s+', ' ', safe).strip()
        return safe if safe else "default.jpg"
    
    print(f"\n🔧 Sanitized Values:")
    cover_safe = sanitize_filename(fate.cover) if fate.cover else "default.jpg"
    wallpaper_safe = sanitize_filename(fate.wallpaper) if fate.wallpaper else "default.jpg"
    
    print(f"   - Cover (safe): {cover_safe}")
    print(f"   - Wallpaper (safe): {wallpaper_safe}")
    
    print(f"\n🌐 URLs:")
    cover_url = f"/static/images/cover/{cover_safe}"
    wallpaper_url = f"/static/images/wallpaper/{wallpaper_safe}"
    
    print(f"   - Cover URL: {cover_url}")
    print(f"   - Wallpaper URL: {wallpaper_url}")
    
    # Check filesystem
    print(f"\n📁 Filesystem Check:")
    base_dir = Path(__file__).parent
    
    # Try multiple possible locations
    possible_cover_paths = [
        base_dir / 'static' / 'images' / 'cover' / cover_safe,
        base_dir / 'main' / 'static' / 'images' / 'cover' / cover_safe,
        base_dir / 'static' / 'images' / 'cover' / fate.cover,  # Original name
    ]
    
    cover_found = False
    for path in possible_cover_paths:
        if path.exists():
            print(f"   ✅ Cover found: {path}")
            cover_found = True
            break
    
    if not cover_found:
        print(f"   ❌ Cover NOT found in any location:")
        for path in possible_cover_paths:
            print(f"      - {path}")
    
    # Check wallpaper
    possible_wallpaper_paths = [
        base_dir / 'static' / 'images' / 'wallpaper' / wallpaper_safe,
        base_dir / 'main' / 'static' / 'images' / 'wallpaper' / wallpaper_safe,
        base_dir / 'static' / 'images' / 'wallpaper' / fate.wallpaper,
    ]
    
    wallpaper_found = False
    for path in possible_wallpaper_paths:
        if path.exists():
            print(f"   ✅ Wallpaper found: {path}")
            wallpaper_found = True
            break
    
    if not wallpaper_found:
        print(f"   ⚠️  Wallpaper NOT found (will fallback to cover)")

# Check sample anime lainnya
print(f"\n" + "=" * 80)
print("SAMPLE CHECK - Other Anime")
print("=" * 80)

sample_anime = Anime.objects.all()[:5]

for anime in sample_anime:
    print(f"\n{anime.title}:")
    print(f"   Cover: {anime.cover}")
    
    # Check if file exists
    base_dir = Path(__file__).parent
    cover_path = base_dir / 'static' / 'images' / 'cover' / anime.cover
    
    if cover_path.exists():
        print(f"   ✅ File exists")
    else:
        # Try sanitized
        import re
        safe_cover = anime.cover.replace(':', '').replace('/', '')
        safe_cover = re.sub(r'\s+', ' ', safe_cover).strip()
        safe_path = base_dir / 'static' / 'images' / 'cover' / safe_cover
        
        if safe_path.exists():
            print(f"   ✅ File exists (sanitized): {safe_cover}")
        else:
            print(f"   ❌ File NOT found")
            print(f"      Tried: {cover_path}")
            print(f"      Tried: {safe_path}")

print("\n" + "=" * 80)
print("RECOMMENDATION")
print("=" * 80)

print("""
Jika cover/wallpaper tidak ditemukan:

1. Check nama file di folder static/images/cover/
   - Harus TIDAK ada titik dua (:)
   - Contoh BENAR: "FateGrand Order Zettai Majuu Sensen Babylonia.jpg"
   - Contoh SALAH: "Fate/Grand Order: Zettai Majuu Sensen Babylonia.jpg"

2. Rename file jika masih ada titik dua:
   python rename_images.py --live

3. Update template untuk pakai sanitize function
""")

print("=" * 80)