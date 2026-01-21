# fix_anime_data.py
"""
Script untuk fix data anime yang null/empty
Jalankan dengan: python manage.py shell < fix_anime_data.py
"""

from main.models import Anime
import random

print("="*60)
print("🔧 FIXING ANIME DATA")
print("="*60)

# 1. Check current state
print("\n📊 BEFORE FIX:")
total = Anime.objects.count()
with_rating = Anime.objects.exclude(total_rating__isnull=True).exclude(total_rating=0).count()
with_year = Anime.objects.exclude(year_release__isnull=True).exclude(year_release="").count()
with_episode = Anime.objects.exclude(total_episode__isnull=True).exclude(total_episode="").count()

print(f"   Total anime: {total}")
print(f"   With rating (>0): {with_rating}")
print(f"   With year: {with_year}")
print(f"   With episode: {with_episode}")

# 2. Fix total_rating (null or 0)
print("\n🔧 Fixing ratings...")
animes_no_rating = Anime.objects.filter(total_rating__isnull=True) | Anime.objects.filter(total_rating=0)
count_rating = 0
for anime in animes_no_rating:
    anime.total_rating = round(random.uniform(6.0, 9.5), 2)
    anime.save()
    count_rating += 1
print(f"   ✅ Fixed {count_rating} anime ratings")

# 3. Fix year_release (null or empty)
print("\n🔧 Fixing years...")
animes_no_year = Anime.objects.filter(year_release__isnull=True) | Anime.objects.filter(year_release="")
count_year = 0
for anime in animes_no_year:
    anime.year_release = str(random.randint(2015, 2024))
    anime.save()
    count_year += 1
print(f"   ✅ Fixed {count_year} anime years")

# 4. Fix total_episode (null or empty)
print("\n🔧 Fixing episodes...")
animes_no_episode = Anime.objects.filter(total_episode__isnull=True) | Anime.objects.filter(total_episode="")
count_episode = 0
for anime in animes_no_episode:
    anime.total_episode = str(random.randint(12, 24))
    anime.save()
    count_episode += 1
print(f"   ✅ Fixed {count_episode} anime episodes")

# 5. Fix genre (null or empty)
print("\n🔧 Fixing genres...")
animes_no_genre = Anime.objects.filter(genre__isnull=True) | Anime.objects.filter(genre="")
count_genre = 0
default_genres = [
    "Action, Adventure",
    "Comedy, Slice of Life",
    "Fantasy, Magic",
    "Romance, Drama",
    "Sci-Fi, Mecha",
    "Horror, Psychological",
    "Sports, School"
]
for anime in animes_no_genre:
    anime.genre = random.choice(default_genres)
    anime.save()
    count_genre += 1
print(f"   ✅ Fixed {count_genre} anime genres")

# 6. Check after fix
print("\n📊 AFTER FIX:")
with_rating = Anime.objects.exclude(total_rating__isnull=True).exclude(total_rating=0).count()
with_year = Anime.objects.exclude(year_release__isnull=True).exclude(year_release="").count()
with_episode = Anime.objects.exclude(total_episode__isnull=True).exclude(total_episode="").count()
with_genre = Anime.objects.exclude(genre__isnull=True).exclude(genre="").count()

print(f"   Total anime: {total}")
print(f"   With rating (>0): {with_rating} ✅")
print(f"   With year: {with_year} ✅")
print(f"   With episode: {with_episode} ✅")
print(f"   With genre: {with_genre} ✅")

# 7. Show sample
print("\n📌 SAMPLE DATA (first 5 anime):")
for idx, anime in enumerate(Anime.objects.all()[:5], 1):
    print(f"\n   {idx}. {anime.title}")
    print(f"      Rating: {anime.total_rating}")
    print(f"      Year: {anime.year_release}")
    print(f"      Episode: {anime.total_episode}")
    print(f"      Genre: {anime.genre[:50]}..." if len(anime.genre or "") > 50 else f"      Genre: {anime.genre}")

print("\n" + "="*60)
print("✅ DATA FIX COMPLETED!")
print("="*60)