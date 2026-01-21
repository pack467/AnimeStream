# main/recommender.py
"""
Sistem Rekomendasi Anime menggunakan SVD (Singular Value Decomposition)
Implementasi sesuai dengan dokumen penelitian

TAHAPAN:
1. Pra-processing: Membuat pivot matrix user x anime
2. Normalisasi: Row-centering menggunakan rata-rata user
3. SVD: Dekomposisi matrix menjadi U, Σ, V^T
4. Truncated SVD: Mengambil k faktor terpenting
5. Rekonstruksi: Membangun kembali matrix prediksi
6. Un-normalisasi: Mengembalikan ke skala rating asli
7. Rekomendasi: Mengambil Top-N item yang belum dirating
"""

import re
import numpy as np
import pandas as pd
from django.core.cache import cache
from django.db.models import Q
from .models import Anime, UserAnimeRating


# ================================================
# 1. HELPER FUNCTIONS
# ================================================

def clean_title(s: str) -> str:
    """
    Membersihkan judul anime untuk konsistensi
    """
    s = (s or "").lower().strip()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[^\w\s:!()\-.,'&/]+", "", s)
    return s.strip()


def confidence_label(pred: float) -> str:
    """
    Memberikan label confidence berdasarkan prediksi rating
    """
    if pred >= 9.0:
        return "very high"
    if pred >= 8.0:
        return "high"
    if pred >= 7.0:
        return "medium"
    return "low"


# ================================================
# 2. DATA PREPARATION - PIVOT MATRIX
# ================================================

def build_pivot_matrix():
    """
    Membuat pivot matrix user x anime dari database
    
    Returns:
        tuple: (pivot_df, user_ids, anime_objects)
        - pivot_df: DataFrame dengan index=user_id, columns=anime_title
        - user_ids: List of user IDs yang terurut
        - anime_objects: List of Anime objects yang terurut berdasarkan title_clean
    """
    # Ambil semua rating dari database
    ratings_qs = UserAnimeRating.objects.select_related("anime", "user").all()
    
    if not ratings_qs.exists():
        return None, [], []
    
    # Convert ke DataFrame untuk pivot
    data = []
    for r in ratings_qs:
        data.append({
            'user_id': r.user_id,
            'anime_title': r.anime.title_clean,
            'rating': float(r.rating)
        })
    
    df = pd.DataFrame(data)
    
    # Buat pivot matrix: baris=user, kolom=anime, nilai=rating
    pivot_df = df.pivot_table(
        index='user_id',
        columns='anime_title',
        values='rating',
        aggfunc='last'  # Ambil rating terakhir jika ada duplikat
    )
    
    # Dapatkan anime objects yang terurut sesuai kolom pivot
    anime_titles = pivot_df.columns.tolist()
    anime_objects = []
    for title in anime_titles:
        anime = Anime.objects.filter(title_clean=title).first()
        if anime:
            anime_objects.append(anime)
    
    user_ids = pivot_df.index.tolist()
    
    return pivot_df, user_ids, anime_objects


# ================================================
# 3. NORMALISASI MATRIX
# ================================================

def normalize_matrix(A_df):
    """
    Normalisasi matrix menggunakan row-centering (user mean normalization)
    
    Tahapan:
    1. Replace 0 dengan NaN (tidak ada rating)
    2. Hitung mean per anime untuk fill NaN
    3. Hitung mean per user (mu_i)
    4. Row-centering: A_centered = A - mu_i
    
    Args:
        A_df: DataFrame pivot matrix (user x anime)
    
    Returns:
        tuple: (A_centered, user_means, A_filled)
    """
    A = A_df.values.copy()
    
    # Replace 0 dengan NaN
    A[A == 0] = np.nan
    
    # Hitung mean per anime (kolom) - untuk fill missing values
    item_means = np.nanmean(A, axis=0)
    global_mean = np.nanmean(A)
    
    # Fill NaN dengan item mean
    A_filled = A.copy()
    for j in range(A.shape[1]):
        mask = np.isnan(A[:, j])
        fill_val = item_means[j] if not np.isnan(item_means[j]) else global_mean
        A_filled[mask, j] = fill_val
    
    # Hitung user mean (mu_i) - rata-rata rating per user
    user_means = np.nanmean(A_filled, axis=1)
    
    # Row-centering: kurangi setiap row dengan user mean
    A_centered = A_filled - user_means[:, np.newaxis]
    
    return A_centered, user_means, A_filled


# ================================================
# 4. SVD DECOMPOSITION
# ================================================

def perform_svd(A_centered, k_factors=8):
    """
    Melakukan SVD decomposition dan truncated SVD
    
    Tahapan:
    1. SVD: A_centered = U @ Σ @ V^T
    2. Truncated SVD: Ambil k faktor terpenting
    3. Rekonstruksi: A_centered_hat_k = U_k @ Σ_k @ V_k^T
    
    Args:
        A_centered: Matrix yang sudah dinormalisasi
        k_factors: Jumlah faktor laten yang digunakan
    
    Returns:
        tuple: (A_centered_hat_k, U, S, Vt)
    """
    # Full SVD
    U, S, Vt = np.linalg.svd(A_centered, full_matrices=False)
    
    # Truncated SVD - ambil k faktor terpenting
    k = min(k_factors, len(S))
    U_k = U[:, :k]
    S_k = np.diag(S[:k])
    Vt_k = Vt[:k, :]
    
    # Rekonstruksi matrix di ruang terpusat (normalized space)
    A_centered_hat_k = U_k @ S_k @ Vt_k
    
    return A_centered_hat_k, U, S, Vt


# ================================================
# 5. UN-NORMALISASI & CLIPPING
# ================================================

def denormalize_and_clip(A_centered_hat_k, user_means, clip_range=(1.0, 10.0)):
    """
    Un-normalisasi: Mengembalikan ke skala rating asli
    
    Tahapan:
    1. Tambahkan kembali user mean: A_hat = A_centered_hat + mu_i
    2. Clip ke rentang rating valid (1-10)
    
    Args:
        A_centered_hat_k: Matrix hasil rekonstruksi SVD
        user_means: Mean rating per user
        clip_range: Rentang valid rating (min, max)
    
    Returns:
        np.array: Matrix prediksi rating final
    """
    # Tambahkan kembali user mean
    A_pred = A_centered_hat_k + user_means[:, np.newaxis]
    
    # Clip ke rentang valid
    A_pred = np.clip(A_pred, clip_range[0], clip_range[1])
    
    return A_pred


# ================================================
# 6. GENERATE RECOMMENDATIONS
# ================================================

def generate_top_n_recommendations(
    user_id,
    A_original,
    A_pred,
    user_ids,
    anime_objects,
    top_n=10,
    min_pred=6.5
):
    """
    Generate Top-N recommendations untuk satu user
    
    Tahapan:
    1. Cari index user di matrix
    2. Ambil prediksi rating untuk semua anime
    3. Filter: hanya anime yang belum dirating (NaN di A_original)
    4. Sort berdasarkan prediksi rating tertinggi
    5. Ambil Top-N
    
    Args:
        user_id: ID user yang ingin diberi rekomendasi
        A_original: Matrix rating asli (ada NaN)
        A_pred: Matrix prediksi hasil SVD
        user_ids: List user IDs
        anime_objects: List Anime objects
        top_n: Jumlah rekomendasi
        min_pred: Minimum prediksi rating untuk direkomendasikan
    
    Returns:
        list: List of dicts dengan format {rank, anime, genres, predicted_rating, confidence}
    """
    # Cari index user
    if user_id not in user_ids:
        return []
    
    user_idx = user_ids.index(user_id)
    
    # Ambil baris prediksi untuk user ini
    user_preds = A_pred[user_idx, :]
    
    # Ambil baris asli untuk cek item yang sudah dirating
    user_original = A_original[user_idx, :]
    
    # Cari anime yang belum dirating (NaN di original)
    unrated_mask = np.isnan(user_original)
    
    # Buat list kandidat: (anime_idx, predicted_rating)
    candidates = []
    for anime_idx in range(len(anime_objects)):
        if unrated_mask[anime_idx]:
            pred_rating = user_preds[anime_idx]
            if pred_rating >= min_pred:
                candidates.append((anime_idx, pred_rating))
    
    # Sort berdasarkan prediksi rating (tertinggi dulu)
    candidates.sort(key=lambda x: x[1], reverse=True)
    
    # Ambil Top-N
    results = []
    for rank, (anime_idx, pred_rating) in enumerate(candidates[:top_n], start=1):
        anime = anime_objects[anime_idx]
        
        # Split genre menjadi list
        genres = [g.strip() for g in (anime.genre or "").split(",") if g.strip()]
        
        results.append({
            "rank": rank,
            "anime": anime,
            "genres": genres,
            "predicted_rating": round(pred_rating, 2),
            "confidence": confidence_label(pred_rating),
        })
    
    return results


# ================================================
# 7. MAIN FUNCTION - GET RECOMMENDATIONS
# ================================================

def get_recommendations_for_user(user, top_n=1000, k_factors=8, min_pred=6.5):
    """
    Main function untuk mendapatkan rekomendasi anime untuk user
    
    Implementasi lengkap SVD:
    1. Build pivot matrix dari database
    2. Normalisasi (row-centering dengan user mean)
    3. SVD decomposition
    4. Truncated SVD (k faktor)
    5. Rekonstruksi matrix
    6. Un-normalisasi
    7. Generate Top-N recommendations
    
    Cold-start handling:
    - User baru (<3 rating) → fallback ke popular anime
    - Tidak ada data rating → fallback ke popular anime
    
    Args:
        user: Django User object
        top_n: Jumlah rekomendasi (default 1000 untuk konsistensi)
        k_factors: Jumlah faktor laten SVD (default 8)
        min_pred: Minimum prediksi rating (default 6.5)
    
    Returns:
        list: List rekomendasi dengan format {rank, anime, genres, predicted_rating, confidence}
    """
    # Cache key
    cache_key = f"rec_user_{user.id}_k{k_factors}_n{top_n}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    # ================================================
    # STEP 1: BUILD PIVOT MATRIX
    # ================================================
    pivot_df, user_ids, anime_objects = build_pivot_matrix()
    
    if pivot_df is None or len(user_ids) == 0:
        # Fallback: Tidak ada data rating sama sekali
        return _fallback_popular_recommendations(top_n)
    
    # ================================================
    # STEP 2: CHECK USER COLD-START
    # ================================================
    if user.id not in user_ids:
        # User belum pernah rating sama sekali
        return _fallback_popular_recommendations(top_n)
    
    user_idx = user_ids.index(user.id)
    user_row = pivot_df.iloc[user_idx].values
    rated_count = int(np.sum(~np.isnan(user_row)))
    
    if rated_count < 3:
        # Cold-start: User baru rating < 3 anime
        results = _fallback_popular_recommendations(top_n)
        cache.set(cache_key, results, 1800)  # Cache 30 menit untuk cold-start
        return results
    
    # ================================================
    # STEP 3: NORMALISASI
    # ================================================
    A_centered, user_means, A_filled = normalize_matrix(pivot_df)
    
    # ================================================
    # STEP 4 & 5: SVD & TRUNCATED SVD
    # ================================================
    A_centered_hat_k, U, S, Vt = perform_svd(A_centered, k_factors)
    
    # ================================================
    # STEP 6: UN-NORMALISASI & CLIPPING
    # ================================================
    A_pred = denormalize_and_clip(A_centered_hat_k, user_means, clip_range=(1.0, 10.0))
    
    # ================================================
    # STEP 7: GENERATE RECOMMENDATIONS
    # ================================================
    A_original = pivot_df.values  # Matrix dengan NaN untuk yang belum dirating
    
    results = generate_top_n_recommendations(
        user_id=user.id,
        A_original=A_original,
        A_pred=A_pred,
        user_ids=user_ids,
        anime_objects=anime_objects,
        top_n=top_n,
        min_pred=min_pred
    )
    
    # Cache 1 jam
    cache.set(cache_key, results, 3600)
    
    return results


# ================================================
# 8. FALLBACK FUNCTION
# ================================================

def _fallback_popular_recommendations(top_n=10):
    """
    Fallback untuk cold-start atau tidak ada data:
    Tampilkan anime populer (berdasarkan total_rating)
    """
    popular = Anime.objects.filter(
        total_rating__isnull=False
    ).exclude(
        total_rating=0
    ).order_by("-total_rating")[:top_n]
    
    results = []
    for rank, anime in enumerate(popular, start=1):
        genres = [g.strip() for g in (anime.genre or "").split(",") if g.strip()]
        results.append({
            "rank": rank,
            "anime": anime,
            "genres": genres,
            "predicted_rating": round(float(anime.total_rating), 2),
            "confidence": "high",
        })
    
    return results


# ================================================
# 9. UTILITY: GET USER RATING COUNT
# ================================================

def get_user_rating_count(user):
    """
    Mendapatkan jumlah anime yang sudah dirating user
    """
    return UserAnimeRating.objects.filter(user=user).count()


# ================================================
# 10. UTILITY: INVALIDATE CACHE
# ================================================

def invalidate_user_recommendations_cache(user_id):
    """
    Invalidate cache rekomendasi user ketika ada perubahan rating
    """
    # Hapus berbagai variasi cache
    for k in [8, 10]:
        for n in [6, 10, 1000]:
            cache_key = f"rec_user_{user_id}_k{k}_n{n}"
            cache.delete(cache_key)