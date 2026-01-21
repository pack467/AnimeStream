# main/views_widgets.py
from django.http import JsonResponse
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from django.templatetags.static import static

from .models import Anime, AnimeViewLog, EpisodeRelease


def api_top_views(request):
    """
    API endpoint untuk Top Views widget
    Query parameter: timeframe = day/week/month
    """
    timeframe = request.GET.get("timeframe", "day")
    
    # Tentukan rentang waktu
    now = timezone.now()
    if timeframe == "day":
        start_time = now - timedelta(days=1)
    elif timeframe == "week":
        start_time = now - timedelta(weeks=1)
    elif timeframe == "month":
        start_time = now - timedelta(days=30)
    else:
        start_time = now - timedelta(days=1)
    
    # Query anime yang paling banyak dilihat
    top_anime = (
        AnimeViewLog.objects
        .filter(viewed_at__gte=start_time)
        .values("anime")
        .annotate(view_count=Count("anime"))
        .order_by("-view_count")[:20]  # ambil 20 teratas
    )
    
    # Ambil data anime lengkap
    data = []
    for item in top_anime:
        try:
            anime = Anime.objects.get(id=item["anime"])
            data.append({
                "anime_id": anime.id,  # ✅ tambah ini
                "title": anime.title,
                "image": f"/static/images/cover/{anime.cover}" if anime.cover else "/static/images/cover/default.jpg",
                "views": item["view_count"]
            })
        except Anime.DoesNotExist:
            continue
    
    # Jika tidak ada data views, ambil anime dengan rating tertinggi sebagai fallback
    if not data:
        fallback_anime = Anime.objects.exclude(total_rating__isnull=True).order_by("-total_rating")[:20]
        for anime in fallback_anime:
            data.append({
                "anime_id": anime.id,  # ✅ tambah ini
                "title": anime.title,
                "image": f"/static/images/cover/{anime.cover}" if anime.cover else "/static/images/cover/default.jpg",
                "views": int(anime.total_rating * 1000)  # simulasi views dari rating
            })
    
    return JsonResponse({
        "status": "success",
        "timeframe": timeframe,
        "data": data
    })


def api_today(request):
    """
    API endpoint untuk Today widget (episode terbaru hari ini)
    """
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Query episode yang rilis hari ini
    today_episodes = (
        EpisodeRelease.objects
        .filter(released_at__gte=today_start)
        .select_related("anime")
        .order_by("-released_at")[:20]  # ambil 20 teratas
    )
    
    data = []
    for ep in today_episodes:
        # Hitung waktu relatif
        time_diff = now - ep.released_at
        hours = int(time_diff.total_seconds() / 3600)
        
        if hours < 1:
            time_str = f"{int(time_diff.total_seconds() / 60)} minutes ago"
        elif hours < 24:
            time_str = f"{hours} hours ago"
        else:
            days = int(time_diff.total_seconds() / 86400)
            time_str = f"{days} days ago"
        
        data.append({
            "anime_id": ep.anime.id,  # ✅ tambah ini
            "title": ep.anime.title,
            "image": f"/static/images/cover/{ep.anime.cover}" if ep.anime.cover else "/static/images/cover/default.jpg",
            "episode": ep.episode,
            "time": time_str
        })
    
    # Jika tidak ada episode hari ini, ambil episode terbaru dalam 7 hari terakhir
    if not data:
        week_start = now - timedelta(days=7)
        recent_episodes = (
            EpisodeRelease.objects
            .filter(released_at__gte=week_start)
            .select_related("anime")
            .order_by("-released_at")[:20]
        )
        
        for ep in recent_episodes:
            time_diff = now - ep.released_at
            hours = int(time_diff.total_seconds() / 3600)
            
            if hours < 24:
                time_str = f"{hours} hours ago"
            else:
                days = int(time_diff.total_seconds() / 86400)
                time_str = f"{days} days ago"
            
            data.append({
                "anime_id": ep.anime.id,  # ✅ tambah ini
                "title": ep.anime.title,
                "image": f"/static/images/cover/{ep.anime.cover}" if ep.anime.cover else "/static/images/cover/default.jpg",
                "episode": ep.episode,
                "time": time_str
            })
    
    # Jika masih tidak ada data, buat data dummy dari anime terbaru
    if not data:
        recent_anime = Anime.objects.exclude(year_release__isnull=True).order_by("-year_release")[:10]
        for idx, anime in enumerate(recent_anime):
            data.append({
                "anime_id": anime.id,  # ✅ tambah ini
                "title": anime.title,
                "image": f"/static/images/cover/{anime.cover}" if anime.cover else "/static/images/cover/default.jpg",
                "episode": "Episode 1",
                "time": f"{idx + 1} hours ago"
            })
    
    return JsonResponse({
        "status": "success",
        "data": data
    })