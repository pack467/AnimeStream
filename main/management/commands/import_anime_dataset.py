import re
import pandas as pd

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from main.models import Anime, UserAnimeRating


def clean_title(s: str) -> str:
    s = (s or "").lower().strip()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[^\w\s:!()\-.,'&/]+", "", s)  # buang karakter aneh berlebih
    return s.strip()


class Command(BaseCommand):
    help = "Import Tabel Anime.xlsx dan Rating Anime User.xlsx ke MySQL (Django ORM)."

    def add_arguments(self, parser):
        parser.add_argument("--anime", default="Tabel Anime.xlsx")
        parser.add_argument("--rating", default="Rating_Anime_User.xlsx")

    def handle(self, *args, **opts):
        anime_path = opts["anime"]
        rating_path = opts["rating"]

        # ---------------------------
        # 1) Import Anime
        # ---------------------------
        df_anime = pd.read_excel(anime_path)
        created_a = 0
        updated_a = 0

        for _, row in df_anime.iterrows():
            title = str(row.get("Judul Anime", "")).strip()
            if not title or title.lower() == "nan":
                continue

            defaults = {
                "title_clean": clean_title(title),
                "genre": str(row.get("Genre", "")).strip(),
                "total_episode": str(row.get("Total Episode", "")).strip(),
                "anime_type": str(row.get("Tipe", "")).strip(),
                "year_release": str(row.get("Tahun Rilis", "")).strip(),
                "content_rating": str(row.get("Konten Rating", "")).strip(),
                "status": str(row.get("Status", "")).strip(),
                "total_rating": float(row.get("Total Rating", 0) or 0),
                "cover": str(row.get("Cover", "")).strip(),
                "wallpaper": str(row.get("Wallpaper", "")).strip(),
            }

            obj, created = Anime.objects.update_or_create(title=title, defaults=defaults)
            created_a += 1 if created else 0
            updated_a += 0 if created else 1

        # ---------------------------
        # 2) Import Rating
        # ---------------------------
        df_r = pd.read_excel(rating_path)
        created_r = 0
        updated_r = 0
        skipped_r = 0

        # mapping title_clean -> Anime
        anime_map = {a.title_clean: a for a in Anime.objects.all()}

        for _, row in df_r.iterrows():
            username = str(row.get("nama_user", "")).strip()
            title = str(row.get("judul_anime", "")).strip()
            rating = row.get("rating_user", None)

            # skip kalau rating kosong / NaN
            if rating is None or (isinstance(rating, float) and pd.isna(rating)):
                skipped_r += 1
                continue

            # skip kalau username / title kosong
            if not username or username.lower() == "nan" or not title or title.lower() == "nan":
                skipped_r += 1
                continue

            # pastikan rating angka valid
            try:
                rating_val = float(rating)
            except Exception:
                skipped_r += 1
                continue

            if rating_val < 1.0 or rating_val > 10.0:
                skipped_r += 1
                continue

            user = User.objects.filter(username__iexact=username).first()
            if not user:
                skipped_r += 1
                continue

            a = anime_map.get(clean_title(title))
            if not a:
                # kalau ada mismatch judul, skip dulu (bisa kita mapping belakangan)
                skipped_r += 1
                continue

            obj, created = UserAnimeRating.objects.update_or_create(
                user=user,
                anime=a,
                defaults={"rating": rating_val}
            )
            created_r += 1 if created else 0
            updated_r += 0 if created else 1

        self.stdout.write(self.style.SUCCESS("=== IMPORT SELESAI ==="))
        self.stdout.write(f"Anime   Created: {created_a} | Updated: {updated_a}")
        self.stdout.write(f"Rating  Created: {created_r} | Updated: {updated_r} | Skipped: {skipped_r}")
