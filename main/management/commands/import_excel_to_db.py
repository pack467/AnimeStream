# main/management/commands/import_excel_to_db.py
import re
import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction

from main.models import Anime, UserAnimeRating


def clean_title(s: str) -> str:
    s = (s or "").lower().strip()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[^\w\s:!()\-.,'&/]+", "", s)
    return s.strip()


class Command(BaseCommand):
    help = "Import Excel ke database (Anime meta atau rating matrix)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--mode",
            choices=["meta", "ratings"],
            default="meta",
            help="meta = import tabel Anime, ratings = import UserAnimeRating matrix",
        )
        parser.add_argument(
            "--file",
            type=str,
            required=True,
            help="Path ke file Excel (.xlsx)",
        )
        parser.add_argument(
            "--create-users",
            action="store_true",
            help="(mode=ratings) Kalau user belum ada, buat user baru otomatis.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        mode = options["mode"]
        filepath = options["file"]
        create_users = options["create_users"]

        try:
            df = pd.read_excel(filepath)
        except Exception as e:
            raise CommandError(f"Gagal membaca excel: {e}")

        if mode == "meta":
            self.import_meta(df)
        else:
            self.import_ratings(df, create_users=create_users)

    def import_meta(self, df: pd.DataFrame):
        required = [
            "Judul Anime", "Genre", "Total Episode", "Tipe", "Tahun Rilis",
            "Konten Rating", "Status", "Total Rating", "Cover", "Wallpaper"
        ]
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise CommandError(f"Kolom kurang di Excel: {missing}")

        created = 0
        updated = 0
        skipped = 0

        for _, row in df.iterrows():
            title = str(row.get("Judul Anime") or "").strip()
            if not title or title.lower() == "nan":
                skipped += 1
                continue

            genre = str(row.get("Genre") or "").strip()
            total_episode = str(row.get("Total Episode") or "").strip()
            anime_type = str(row.get("Tipe") or "").strip()
            year_release = str(row.get("Tahun Rilis") or "").strip()
            content_rating = str(row.get("Konten Rating") or "").strip()
            status = str(row.get("Status") or "").strip()

            # rating
            tr = row.get("Total Rating")
            try:
                total_rating = float(tr) if tr is not None and str(tr).lower() != "nan" else 0.0
            except Exception:
                total_rating = 0.0

            cover = str(row.get("Cover") or "").strip()
            wallpaper = str(row.get("Wallpaper") or "").strip()

            obj, is_created = Anime.objects.update_or_create(
                title=title,
                defaults={
                    "title_clean": clean_title(title),
                    "genre": genre,
                    "total_episode": total_episode,
                    "anime_type": anime_type,
                    "year_release": year_release,
                    "content_rating": content_rating,
                    "status": status,
                    "total_rating": total_rating,
                    "cover": cover,
                    "wallpaper": wallpaper,
                },
            )
            if is_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(self.style.SUCCESS(
            f"[META] Selesai. created={created}, updated={updated}, skipped={skipped}"
        ))

    def import_ratings(self, df: pd.DataFrame, create_users: bool):
        # Format file kamu: kolom pertama = user_name, kolom lain = judul anime
        if "user_name" not in df.columns:
            raise CommandError("File ratings harus punya kolom 'user_name'.")

        User = get_user_model()

        # Pastikan semua anime title kolom sudah ada di DB (biar cepat mapping)
        anime_titles = [c for c in df.columns if c != "user_name"]
        anime_map = {
            a.title: a.id
            for a in Anime.objects.filter(title__in=anime_titles).only("id", "title")
        }

        missing_anime_cols = [t for t in anime_titles if t not in anime_map]
        if missing_anime_cols:
            self.stdout.write(self.style.WARNING(
                f"[RATINGS] Ada {len(missing_anime_cols)} kolom anime yang belum ada di tabel Anime. "
                f"Contoh: {missing_anime_cols[:5]}"
            ))

        created = 0
        updated = 0
        skipped_users = 0
        skipped_cells = 0

        # Biar efisien: cache user id
        user_cache = {}

        for _, row in df.iterrows():
            username = str(row.get("user_name") or "").strip()
            if not username or username.lower() == "nan":
                skipped_users += 1
                continue

            user_id = user_cache.get(username)
            if user_id is None:
                u = User.objects.filter(username=username).only("id").first()
                if not u:
                    if not create_users:
                        skipped_users += 1
                        continue
                    u = User.objects.create_user(username=username, password=None)
                user_cache[username] = u.id
                user_id = u.id

            # Loop semua kolom anime rating
            for title in anime_titles:
                anime_id = anime_map.get(title)
                if not anime_id:
                    skipped_cells += 1
                    continue

                rating = row.get(title, None)

                # skip kosong/NaN
                if rating is None or (isinstance(rating, float) and pd.isna(rating)):
                    continue

                try:
                    rating_val = float(rating)
                except Exception:
                    skipped_cells += 1
                    continue

                if rating_val < 1.0 or rating_val > 10.0:
                    skipped_cells += 1
                    continue

                obj, is_created = UserAnimeRating.objects.update_or_create(
                    user_id=user_id,
                    anime_id=anime_id,
                    defaults={"rating": rating_val},
                )
                if is_created:
                    created += 1
                else:
                    updated += 1

        self.stdout.write(self.style.SUCCESS(
            f"[RATINGS] Selesai. created={created}, updated={updated}, "
            f"skipped_users={skipped_users}, skipped_cells={skipped_cells}"
        ))
