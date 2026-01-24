from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q

import pandas as pd
import math

from main.models import Anime, UserAnimeRating


def norm_col(s: str) -> str:
    """
    Normalisasi nama kolom:
    - lower
    - trim
    - spasi & '-' jadi '_'
    - hapus double underscore
    """
    s = (s or "").strip().lower()
    s = s.replace("-", "_").replace(" ", "_")
    while "__" in s:
        s = s.replace("__", "_")
    return s


def find_col(normed_cols, aliases):
    """
    Cari kolom berdasarkan alias, setelah kolom dinormalisasi.
    normed_cols: dict {normalized_name: original_name}
    aliases: list[str] alias normalized
    """
    for a in aliases:
        a = norm_col(a)
        if a in normed_cols:
            return normed_cols[a]
    return None


class Command(BaseCommand):
    help = "Import rating anime user dari file Excel ke database."

    def add_arguments(self, parser):
        parser.add_argument("--file", required=True, help="Path file Excel (mis. 'Rating Anime User.xlsx')")
        parser.add_argument("--create-users", action="store_true", help="Buat user baru jika belum ada")

    def handle(self, *args, **opts):
        file_path = opts["file"]
        create_users = opts["create_users"]

        try:
            df = pd.read_excel(file_path)
        except Exception as e:
            raise CommandError(f"Gagal membaca file Excel: {e}")

        if df.empty:
            raise CommandError("File Excel kosong.")

        # ✅ Bersihkan baris yang sepenuhnya kosong
        df = df.dropna(how="all")

        if df.empty:
            raise CommandError("File Excel kosong setelah menghapus baris kosong.")

        # mapping normalized -> original
        normed_cols = {norm_col(c): c for c in df.columns}

        # ✅ Tambahkan dukungan kolom yang kamu punya:
        user_col = find_col(normed_cols, ["user_name", "username", "user", "nama_user", "nama user"])
        title_col = find_col(normed_cols, ["title", "anime_title", "anime", "judul", "nama_anime", "judul_anime", "judul anime"])
        rating_col = find_col(normed_cols, ["rating_user", "rating", "score", "nilai"])

        missing = []
        if not user_col:
            missing.append("username: butuh salah satu dari user_name/username/user/nama_user")
        if not title_col:
            missing.append("title anime: butuh salah satu dari title/anime_title/anime/judul/nama_anime/judul_anime")
        if not rating_col:
            missing.append("rating: butuh salah satu dari rating_user/rating/score/nilai")

        if missing:
            detected = list(df.columns)
            raise CommandError(
                "Kolom wajib tidak ditemukan.\n"
                + "\n".join(missing)
                + f"\nKolom yang terdeteksi: {detected}"
            )

        # ✅ Konversi kolom rating ke numeric, NaN untuk yang invalid
        df[rating_col] = pd.to_numeric(df[rating_col], errors="coerce")

        User = get_user_model()

        total_rows = len(df)
        inserted = 0
        updated = 0
        skipped = 0
        created_users = 0
        not_found_anime = 0

        # cache biar cepat
        user_cache = {}
        anime_cache = {}

        def get_or_create_user(username):
            nonlocal created_users
            username = (username or "").strip()
            if not username:
                return None

            if username in user_cache:
                return user_cache[username]

            u = User.objects.filter(username=username).first()
            if not u and create_users:
                # password random, user bisa reset belakangan
                u = User.objects.create_user(username=username, password=None)
                created_users += 1

            user_cache[username] = u
            return u

        def get_anime_by_title(title):
            title = (title or "").strip()
            if not title:
                return None

            if title in anime_cache:
                return anime_cache[title]

            # cari paling aman: title exact, lalu icontains fallback
            a = Anime.objects.filter(title=title).first()
            if not a:
                a = Anime.objects.filter(title__iexact=title).first()
            if not a:
                a = Anime.objects.filter(title__icontains=title).first()

            anime_cache[title] = a
            return a

        with transaction.atomic():
            for i, row in df.iterrows():
                username = str(row.get(user_col, "")).strip()
                title = str(row.get(title_col, "")).strip()
                rating_raw = row.get(rating_col, None)

                # skip kalau username atau title kosong
                if not username or not title:
                    skipped += 1
                    continue

                # ✅ skip kalau rating kosong/NaN (Excel sering jadi NaN)
                if rating_raw is None or (isinstance(rating_raw, float) and pd.isna(rating_raw)):
                    skipped += 1
                    continue

                # ✅ convert ke float
                try:
                    rating_val = float(rating_raw)
                except Exception:
                    skipped += 1
                    continue

                # ✅ kalau rating jadi NaN/inf, skip
                if math.isnan(rating_val) or math.isinf(rating_val):
                    skipped += 1
                    continue

                # batas rating
                if rating_val < 1.0 or rating_val > 10.0:
                    skipped += 1
                    continue

                user = get_or_create_user(username)
                if not user:
                    skipped += 1
                    continue

                anime = get_anime_by_title(title)
                if not anime:
                    not_found_anime += 1
                    continue

                obj, is_created = UserAnimeRating.objects.update_or_create(
                    user=user,
                    anime=anime,
                    defaults={"rating": rating_val},
                )
                if is_created:
                    inserted += 1
                else:
                    updated += 1

        self.stdout.write(self.style.SUCCESS("✅ Import selesai"))
        self.stdout.write(f"Total baris: {total_rows}")
        self.stdout.write(f"Insert rating baru: {inserted}")
        self.stdout.write(f"Update rating lama: {updated}")
        self.stdout.write(f"User dibuat: {created_users}")
        self.stdout.write(f"Anime tidak ditemukan: {not_found_anime}")
        self.stdout.write(f"Skip: {skipped}")