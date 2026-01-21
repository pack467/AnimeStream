# main/utils.py
"""
Utility functions untuk AniMEStream - Handle filename dengan karakter special
"""

import re


def sanitize_filename(filename):
    """
    Sanitize filename untuk filesystem (handle karakter yang tidak bisa di filesystem)
    
    Karakter yang tidak diperbolehkan:
    - Windows: < > : " / \ | ? *
    - Linux/Mac: /
    
    Strategy: HAPUS titik dua (:) dan karakter illegal lainnya
    
    Args:
        filename (str): Original filename dari database (bisa ada titik dua)
                       Contoh: "Dr. STONE: STONE WARS.jpg"
    
    Returns:
        str: Safe filename untuk filesystem
            Contoh: "Dr. STONE STONE WARS.jpg"
    
    Examples:
        >>> sanitize_filename("Dr. STONE: STONE WARS.jpg")
        'Dr. STONE STONE WARS.jpg'
        
        >>> sanitize_filename("Re:Zero kara Hajimeru Isekai Seikatsu.jpg")
        'ReZero kara Hajimeru Isekai Seikatsu.jpg'
        
        >>> sanitize_filename("Fate/Grand Order: Zettai Majuu Sensen Babylonia.jpg")
        'FateGrand Order Zettai Majuu Sensen Babylonia.jpg'
    """
    if not filename:
        return "default.jpg"
    
    # HAPUS titik dua (paling penting untuk Windows!)
    safe_name = filename.replace(':', '')
    
    # HAPUS slash (forward dan backward)
    safe_name = safe_name.replace('/', '')
    safe_name = safe_name.replace('\\', '')
    
    # HAPUS karakter illegal lainnya
    safe_name = safe_name.replace('<', '')
    safe_name = safe_name.replace('>', '')
    safe_name = safe_name.replace('"', '')
    safe_name = safe_name.replace('|', '')
    safe_name = safe_name.replace('?', '')
    safe_name = safe_name.replace('*', '')
    
    # Clean up multiple spaces
    safe_name = re.sub(r'\s+', ' ', safe_name)
    safe_name = safe_name.strip()
    
    # Fallback jika jadi kosong
    if not safe_name or safe_name in ('.jpg', '.png', '.webp', '.gif'):
        return "default.jpg"
    
    return safe_name


def get_cover_url(anime):
    """
    Get URL untuk cover image dengan sanitized filename
    
    Args:
        anime: Anime model instance
    
    Returns:
        str: URL ke cover image
    """
    if not anime or not hasattr(anime, 'cover') or not anime.cover:
        return "/static/images/cover/default.jpg"
    
    # Jika sudah full URL (http/https), return as-is
    if anime.cover.startswith(('http://', 'https://')):
        return anime.cover
    
    # Sanitize filename
    safe_filename = sanitize_filename(anime.cover)
    
    # Build URL
    return f"/static/images/cover/{safe_filename}"


def get_wallpaper_url(anime):
    """
    Get URL untuk wallpaper image dengan sanitized filename
    
    Args:
        anime: Anime model instance
    
    Returns:
        str: URL ke wallpaper image (fallback ke cover jika wallpaper kosong)
    """
    if not anime:
        return "/static/images/wallpaper/default.jpg"
    
    # Try wallpaper first
    if hasattr(anime, 'wallpaper') and anime.wallpaper and anime.wallpaper.strip():
        wallpaper_filename = anime.wallpaper
        
        # Jika sudah full URL
        if wallpaper_filename.startswith(('http://', 'https://')):
            return wallpaper_filename
        
        # Sanitize filename
        safe_filename = sanitize_filename(wallpaper_filename)
        return f"/static/images/wallpaper/{safe_filename}"
    
    # Fallback ke cover
    return get_cover_url(anime)


# ============================================================================
# DJANGO TEMPLATE FILTERS
# ============================================================================

from django import template

register = template.Library()


@register.filter(name='cover_url')
def cover_url_filter(anime):
    """
    Template filter untuk get cover URL dengan safe filename
    
    Usage di template:
        <img src="{{ anime|cover_url }}" alt="{{ anime.title }}">
    
    atau
    
        {% load utils %}
        <img src="{{ anime|cover_url }}" alt="Cover">
    """
    return get_cover_url(anime)


@register.filter(name='wallpaper_url')
def wallpaper_url_filter(anime):
    """
    Template filter untuk get wallpaper URL dengan safe filename
    
    Usage di template:
        <div class="hero" style="background-image: url('{{ anime|wallpaper_url }}')">
        </div>
    
    atau
    
        {% load utils %}
        <div style="background: url('{{ anime|wallpaper_url }}')"></div>
    """
    return get_wallpaper_url(anime)


@register.filter(name='sanitize')
def sanitize_filter(filename):
    """
    Template filter untuk sanitize filename
    
    Usage di template:
        {{ anime.cover|sanitize }}
    """
    return sanitize_filename(filename)