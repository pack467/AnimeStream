# debug_data.py
"""
Script untuk debug data di database
Jalankan dengan: python manage.py shell < debug_data.py
"""

from main.models import Anime, AnimeViewLog, EpisodeRelease

print("="*60)
print("🔍 DEBUG DATABASE - CHECKING DATA")
print("="*60)

# 1. Check Anime data
total_anime = Anime.objects.count()
print(f"\n1️⃣  ANIME DATA:")
print(f"   Total anime: {total_anime}")

anime_with_rating = Anime.objects.exclude(total_rating__isnull=True).exclude(total_rating=0).count()
print(f"   Anime with rating (>0): {anime_with_rating}")

anime_with_year = Anime.objects.exclude(year_release__isnull=True).exclude(year_release="").count()
print(f"   Anime with year: {anime_with_year}")

# Check sample anime data
if total_anime > 0:
    sample = Anime.objects.first()
    print(f"\n   📌 Sample anime:")
    print(f"      Title: {sample.title}")
    print(f"      Rating: {sample.total_rating}")
    print(f"      Year: {sample.year_release}")
    print(f"      Episode: {sample.total_episode}")
    print(f"      Genre: {sample.genre}")
    print(f"      Cover: {sample.cover}")
    print(f"      Wallpaper: {sample.wallpaper}")

# 2. Check trending query
print(f"\n2️⃣  TRENDING NOW QUERY:")
trending = Anime.objects.exclude(total_rating__isnull=True).exclude(total_rating=0).exclude(year_release__isnull=True).exclude(year_release="").order_by("-total_rating", "-year_release")[:6]
print(f"   Results: {trending.count()}")
for idx, a in enumerate(trending, 1):
    print(f"   {idx}. {a.title} - Rating: {a.total_rating}, Year: {a.year_release}")

# 3. Check new releases query
print(f"\n3️⃣  NEW RELEASES QUERY:")
new_releases = Anime.objects.exclude(year_release__isnull=True).exclude(year_release="").exclude(total_rating__isnull=True).order_by("-year_release", "-total_rating")[:6]
print(f"   Results: {new_releases.count()}")
for idx, a in enumerate(new_releases, 1):
    print(f"   {idx}. {a.title} - Year: {a.year_release}, Rating: {a.total_rating}")

# 4. Check AnimeViewLog
print(f"\n4️⃣  ANIME VIEW LOG:")
total_views = AnimeViewLog.objects.count()
print(f"   Total view logs: {total_views}")
if total_views > 0:
    recent = AnimeViewLog.objects.order_by("-viewed_at").first()
    print(f"   Latest view: {recent.anime.title} at {recent.viewed_at}")

# 5. Check EpisodeRelease
print(f"\n5️⃣  EPISODE RELEASE:")
total_episodes = EpisodeRelease.objects.count()
print(f"   Total episodes: {total_episodes}")
if total_episodes > 0:
    recent = EpisodeRelease.objects.order_by("-released_at").first()
    print(f"   Latest episode: {recent.anime.title} - {recent.episode} at {recent.released_at}")

print("\n" + "="*60)
print("✅ DEBUG COMPLETE")
print("="*60)