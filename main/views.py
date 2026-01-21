# main/views.py
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST
from django.core.cache import cache
import logging
import re

from .models import Anime, UserAnimeRating, AnimeViewLog, EpisodeRelease
from .recommender import get_recommendations_for_user, invalidate_user_recommendations_cache

# Setup logging
logger = logging.getLogger(__name__)


def parse_episode_count(total_episode_value, default=12):
    """
    Helper function to parse episode count from various string formats
    Examples: "12 eps" -> 12, "24" -> 24, "TBA" -> default, "?" -> default
    """
    s = str(total_episode_value or "").strip().lower()
    if not s or s in {"nan", "none", "tba", "?"}:
        return default

    # ambil angka pertama yang muncul (contoh: "12 eps" -> 12)
    m = re.search(r"(\d+)", s)
    if not m:
        return default

    n = int(m.group(1))
    if n <= 0:
        return default

    return min(n, 60)  # batas aman


def split_genres(genre_str: str):
    """
    Split genre string menjadi list of genres
    """
    return [g.strip() for g in (genre_str or "").split(",") if g.strip()]


def sanitize_filename(filename):
    """
    Sanitize filename untuk filesystem (handle titik dua, slash, dll)
    
    Karakter tidak diperbolehkan di Windows: < > : " / \ | ? *
    
    Examples:
        "Dr. STONE: STONE WARS.jpg" → "Dr. STONE- STONE WARS.jpg"
        "Re:Zero.jpg" → "Re-Zero.jpg"
        "JoJo's Bizarre Adventure: Part 5.jpg" → "JoJo's Bizarre Adventure- Part 5.jpg"
    """
    if not filename:
        return "default.jpg"
    
    import re
    
    # Replace invalid characters
    safe = filename
    safe = safe.replace(':', '-')  # Colon → Dash (PENTING!)
    safe = safe.replace('/', '-')  # Slash → Dash
    safe = safe.replace('\\', '-')  # Backslash → Dash
    safe = safe.replace('|', '-')  # Pipe → Dash
    safe = safe.replace('"', "'")  # Double quote → Single quote
    safe = safe.replace('?', '')   # Question mark → Remove
    safe = safe.replace('*', '')   # Asterisk → Remove
    safe = safe.replace('<', '')   # Less than → Remove
    safe = safe.replace('>', '')   # Greater than → Remove
    
    # Clean up multiple spaces/dashes
    safe = re.sub(r'\s+', ' ', safe)
    safe = re.sub(r'-+', '-', safe)
    safe = re.sub(r'\s*-\s*', '- ', safe)
    safe = safe.strip()
    
    # Fallback
    if not safe or safe in ('.jpg', '.png', '.webp'):
        return "default.jpg"
    
    return safe


def pick_bg(anime: Anime):
    """
    Pilih background hero dengan safe filename handling
    """
    wp = getattr(anime, "wallpaper", None)
    if wp and wp.strip():
        safe_wp = sanitize_filename(wp)
        return ("wallpaper", safe_wp)
    cv = getattr(anime, "cover", None)
    if cv and cv.strip():
        safe_cv = sanitize_filename(cv)
        return ("cover", safe_cv)
    return ("cover", "default.jpg")


@login_required
def home(request):
    """
    Home view with personalized recommendations using SVD
    
    Sections:
    1. Recommended for You - SVD collaborative filtering (Top 6 dari 1000)
    2. Trending Now - High rated anime (rating tertinggi)
    3. New Releases - Latest anime (tahun terbaru)
    4. Hero Carousel - 3 hero items dari masing-masing section
    """
    logger.info(f"Home view accessed by user: {request.user.username}")
    
    # =========================
    # 1) RECOMMENDATIONS (SVD)
    # =========================
    recommendations = []
    try:
        # ✅ Gunakan top_n=1000 untuk konsistensi dengan Search
        all_recommendations = get_recommendations_for_user(
            request.user,
            top_n=1000,
            k_factors=8,
            min_pred=6.5
        )
        # Ambil 6 pertama untuk ditampilkan di home
        recommendations = all_recommendations[:6]
        logger.info(f"✅ SVD Recommendations: {len(recommendations)} items shown from {len(all_recommendations)} total")
        
        # ⚠️ DEBUG: Print untuk verifikasi
        if recommendations:
            logger.info(f"   First recommendation: {recommendations[0]['anime'].title} (rating: {recommendations[0]['predicted_rating']})")
        else:
            logger.warning(f"   ⚠️  No SVD recommendations generated!")
            
    except Exception as e:
        logger.error(f"❌ Error getting SVD recommendations: {e}", exc_info=True)
        recommendations = []

    # ✅ Jika SVD gagal atau tidak ada hasil, gunakan fallback
    if not recommendations:
        logger.warning("⚠️  SVD recommendations empty, using fallback (popular anime)")
        # Fallback: gunakan popular anime
        popular_qs = (
            Anime.objects
            .exclude(total_rating__isnull=True)
            .exclude(total_rating=0)
            .order_by("-total_rating")
        )[:6]
        
        for a in popular_qs:
            recommendations.append({
                "anime": a,
                "genres": split_genres(getattr(a, "genre", "")),
                "predicted_rating": round(float(getattr(a, "total_rating", 0) or 0), 2),
                "confidence": "popular",  # indicator ini fallback
            })
        logger.info(f"   Fallback recommendations: {len(recommendations)} items")

    # =========================
    # 2) TRENDING NOW
    # ⭐ PERBAIKAN: Harus berbeda dari recommendations!
    # =========================
    trending_qs = (
        Anime.objects
        .exclude(total_rating__isnull=True)
        .exclude(total_rating=0)
        .order_by("-total_rating")  # ✅ Rating tertinggi
    )
    
    # ✅ Exclude anime yang sudah ada di recommendations
    recommended_anime_ids = [r['anime'].id for r in recommendations]
    trending_qs = trending_qs.exclude(id__in=recommended_anime_ids)[:6]
    
    logger.info(f"Trending query result: {trending_qs.count()} items")
    
    if not trending_qs.exists():
        trending_qs = Anime.objects.exclude(id__in=recommended_anime_ids)[:6]
        logger.warning(f"Trending fallback: {trending_qs.count()} items")

    trending = []
    for a in trending_qs:
        trending.append({
            "anime": a,
            "genres": split_genres(getattr(a, "genre", "")),
            "predicted_rating": round(float(getattr(a, "total_rating", 0) or 0), 2),
            "confidence": "high",
        })

    # =========================
    # 3) NEW RELEASES
    # =========================
    new_qs = (
        Anime.objects
        .exclude(year_release__isnull=True)
        .exclude(year_release="")
        .order_by("-year_release", "-total_rating")
    )[:6]
    
    logger.info(f"New releases query result: {new_qs.count()} items")
    
    if not new_qs.exists():
        new_qs = Anime.objects.order_by("-total_rating")[:6]
        logger.warning(f"New releases fallback: {new_qs.count()} items")

    new_releases = []
    for a in new_qs:
        new_releases.append({
            "anime": a,
            "genres": split_genres(getattr(a, "genre", "")),
            "predicted_rating": round(float(getattr(a, "total_rating", 0) or 0), 2),
            "confidence": "high",
        })

    # =========================
    # 4) HERO CAROUSEL
    # =========================
    hero_items = []

    # a) Recommended hero
    if recommendations:
        try:
            a = recommendations[0]["anime"]
            kind, bgfile = pick_bg(a)
            hero_items.append({
                "label": "Recommended",
                "badge_genre": (recommendations[0]["genres"][0] if recommendations[0]["genres"] else "Anime"),
                "anime": a,
                "bg_kind": kind,
                "bg_file": bgfile,
            })
            logger.info(f"Hero item added: Recommended - {a.title}")
        except Exception as e:
            logger.error(f"Error creating recommended hero: {e}")

    # b) Trending hero
    if trending:
        try:
            a = trending[0]["anime"]
            kind, bgfile = pick_bg(a)
            hero_items.append({
                "label": "Trending",
                "badge_genre": (trending[0]["genres"][0] if trending[0]["genres"] else "Anime"),
                "anime": a,
                "bg_kind": kind,
                "bg_file": bgfile,
            })
            logger.info(f"Hero item added: Trending - {a.title}")
        except Exception as e:
            logger.error(f"Error creating trending hero: {e}")

    # c) New hero
    if new_releases:
        try:
            a = new_releases[0]["anime"]
            kind, bgfile = pick_bg(a)
            hero_items.append({
                "label": "New",
                "badge_genre": (new_releases[0]["genres"][0] if new_releases[0]["genres"] else "Anime"),
                "anime": a,
                "bg_kind": kind,
                "bg_file": bgfile,
            })
            logger.info(f"Hero item added: New - {a.title}")
        except Exception as e:
            logger.error(f"Error creating new hero: {e}")

    # Fallback jika hero_items masih kosong
    if not hero_items:
        logger.warning("Hero items empty, using fallback")
        fallback_anime = Anime.objects.all()[:3]
        labels = ["Featured", "Popular", "Latest"]
        for idx, anime in enumerate(fallback_anime):
            try:
                kind, bgfile = pick_bg(anime)
                genres = split_genres(getattr(anime, "genre", ""))
                hero_items.append({
                    "label": labels[idx] if idx < len(labels) else "Featured",
                    "badge_genre": genres[0] if genres else "Anime",
                    "anime": anime,
                    "bg_kind": kind,
                    "bg_file": bgfile,
                })
                logger.info(f"Fallback hero item added: {labels[idx]} - {anime.title}")
            except Exception as e:
                logger.error(f"Error creating fallback hero: {e}")

    logger.info(f"✅ Final counts - Recommendations: {len(recommendations)}, Trending: {len(trending)}, New: {len(new_releases)}, Heroes: {len(hero_items)}")

    return render(request, "home/home.html", {
        "recommendations": recommendations,
        "trending": trending,
        "new_releases": new_releases,
        "hero_items": hero_items,
    })


# =========================
# WATCH PAGE
# =========================
@login_required
def watch(request, anime_id: int):
    """
    Halaman watch untuk menonton anime dan memberi rating
    """
    anime = get_object_or_404(Anime, id=anime_id)

    # Catat view (untuk Top Views widget)
    AnimeViewLog.objects.create(anime=anime)

    # Rating user kalau ada
    my_rating_obj = UserAnimeRating.objects.filter(user=request.user, anime=anime).first()
    my_rating = float(my_rating_obj.rating) if my_rating_obj else 0.0

    # Episodes dari EpisodeRelease (kalau ada)
    episodes_qs = EpisodeRelease.objects.filter(anime=anime).order_by("released_at")
    episodes = []
    for idx, ep in enumerate(episodes_qs, start=1):
        episodes.append({
            "number": idx,
            "title": ep.episode,
            "released_at": ep.released_at,
        })

    # Parse episode count
    ep_count = parse_episode_count(anime.total_episode, default=12)

    # Sidebar recommendations: anime rating tinggi selain yang sedang ditonton
    sidebar_recs_qs = Anime.objects.exclude(id=anime.id).order_by("-total_rating")[:3]
    sidebar_recs = []
    for a in sidebar_recs_qs:
        sidebar_recs.append({
            "anime": a,
            "genres": split_genres(a.genre),
        })

    context = {
        "anime": anime,
        "genres": split_genres(anime.genre),
        "user_rating": my_rating,
        "episodes": episodes,
        "ep_count": ep_count,
        "you_might_also_like": sidebar_recs,
    }
    return render(request, "watch/watch.html", context)


# =========================
# API RATE ANIME
# =========================
@require_POST
@login_required
def api_rate_anime(request, anime_id: int):
    """
    API endpoint untuk memberi rating pada anime
    ✅ UPDATED: Invalidasi cache dengan fungsi baru
    """
    anime = get_object_or_404(Anime, id=anime_id)

    try:
        rating_str = (request.POST.get("rating") or "").strip()
        rating_val = float(rating_str)
    except Exception:
        return JsonResponse({"status": "error", "message": "Rating tidak valid"}, status=400)

    # Validasi (1-10)
    if rating_val < 1.0 or rating_val > 10.0:
        return JsonResponse({"status": "error", "message": "Rating harus 1.0 - 10.0"}, status=400)

    # Simpan atau update rating
    UserAnimeRating.objects.update_or_create(
        user=request.user,
        anime=anime,
        defaults={"rating": rating_val}
    )

    # ✅ Invalidasi cache rekomendasi user
    invalidate_user_recommendations_cache(request.user.id)
    
    logger.info(f"✅ User {request.user.username} rated {anime.title}: {rating_val}")

    return JsonResponse({
        "status": "success",
        "message": "Rating tersimpan",
        "rating": rating_val
    })