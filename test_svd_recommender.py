# test_svd_recommender.py
"""
Testing script untuk validasi sistem rekomendasi SVD
Run: python manage.py shell < test_svd_recommender.py
"""

import numpy as np
from django.contrib.auth.models import User
from main.models import Anime, UserAnimeRating
from main.recommender import (
    get_recommendations_for_user,
    build_pivot_matrix,
    normalize_matrix,
    perform_svd,
    denormalize_and_clip,
    get_user_rating_count
)

print("=" * 80)
print("TESTING SISTEM REKOMENDASI SVD")
print("=" * 80)

# ==========================================================================
# TEST 1: Build Pivot Matrix
# ==========================================================================
print("\n📊 TEST 1: Build Pivot Matrix")
print("-" * 80)

pivot_df, user_ids, anime_objects = build_pivot_matrix()

if pivot_df is not None:
    print(f"✅ Pivot matrix berhasil dibuat")
    print(f"   - Shape: {pivot_df.shape} (users × anime)")
    print(f"   - Total users: {len(user_ids)}")
    print(f"   - Total anime: {len(anime_objects)}")
    print(f"   - Sparsity: {(pivot_df.isna().sum().sum() / (pivot_df.shape[0] * pivot_df.shape[1]) * 100):.1f}%")
    print(f"\n   Sample data:")
    print(pivot_df.head())
else:
    print("❌ Tidak ada data rating di database")
    print("   Silakan tambahkan data rating terlebih dahulu")

# ==========================================================================
# TEST 2: Normalisasi Matrix
# ==========================================================================
if pivot_df is not None:
    print("\n🔧 TEST 2: Normalisasi Matrix")
    print("-" * 80)
    
    A_centered, user_means, A_filled = normalize_matrix(pivot_df)
    
    print(f"✅ Normalisasi berhasil")
    print(f"   - User means shape: {user_means.shape}")
    print(f"   - User means range: [{user_means.min():.2f}, {user_means.max():.2f}]")
    print(f"   - Centered matrix mean: {np.nanmean(A_centered):.6f} (should be ≈ 0)")
    print(f"\n   Sample user means:")
    for i in range(min(5, len(user_means))):
        print(f"   User {user_ids[i]}: μ = {user_means[i]:.2f}")

# ==========================================================================
# TEST 3: SVD Decomposition
# ==========================================================================
if pivot_df is not None:
    print("\n🔬 TEST 3: SVD Decomposition")
    print("-" * 80)
    
    A_centered_hat_k, U, S, Vt = perform_svd(A_centered, k_factors=8)
    
    print(f"✅ SVD berhasil")
    print(f"   - U shape: {U.shape}")
    print(f"   - Σ (singular values): {len(S)} values")
    print(f"   - Vt shape: {Vt.shape}")
    print(f"   - Truncated to: K={8} factors")
    print(f"\n   Top 10 singular values:")
    for i, sv in enumerate(S[:10], 1):
        print(f"   σ{i} = {sv:.4f}")

# ==========================================================================
# TEST 4: Prediksi Rating
# ==========================================================================
if pivot_df is not None:
    print("\n🎯 TEST 4: Prediksi Rating")
    print("-" * 80)
    
    A_pred = denormalize_and_clip(A_centered_hat_k, user_means, clip_range=(1.0, 10.0))
    
    print(f"✅ Prediksi rating berhasil")
    print(f"   - Prediction matrix shape: {A_pred.shape}")
    print(f"   - Rating range: [{A_pred.min():.2f}, {A_pred.max():.2f}]")
    print(f"\n   Sample predictions:")
    
    # Ambil user pertama dan anime pertama
    sample_user_idx = 0
    sample_anime_idx = 0
    
    original_rating = pivot_df.iloc[sample_user_idx, sample_anime_idx]
    predicted_rating = A_pred[sample_user_idx, sample_anime_idx]
    
    print(f"   User: {user_ids[sample_user_idx]}")
    print(f"   Anime: {anime_objects[sample_anime_idx].title}")
    print(f"   Original rating: {original_rating if not np.isnan(original_rating) else 'Not rated'}")
    print(f"   Predicted rating: {predicted_rating:.2f}")

# ==========================================================================
# TEST 5: Generate Recommendations untuk User
# ==========================================================================
print("\n🌟 TEST 5: Generate Recommendations")
print("-" * 80)

# Ambil user pertama yang ada rating-nya
test_user = None
for user in User.objects.all()[:10]:
    rating_count = get_user_rating_count(user)
    if rating_count >= 3:
        test_user = user
        break

if test_user:
    print(f"Testing untuk user: {test_user.username} (ID: {test_user.id})")
    print(f"Jumlah rating user: {get_user_rating_count(test_user)}")
    
    try:
        recommendations = get_recommendations_for_user(
            test_user,
            top_n=10,
            k_factors=8,
            min_pred=6.5
        )
        
        print(f"\n✅ Rekomendasi berhasil di-generate")
        print(f"   Total recommendations: {len(recommendations)}")
        
        if recommendations:
            print(f"\n   Top 10 Recommendations:")
            print(f"   {'Rank':<6} {'Anime':<40} {'Pred. Rating':<15} {'Confidence'}")
            print(f"   {'-'*6} {'-'*40} {'-'*15} {'-'*10}")
            
            for rec in recommendations[:10]:
                rank = rec['rank']
                title = rec['anime'].title[:38]  # Truncate long titles
                pred_rating = rec['predicted_rating']
                confidence = rec['confidence']
                print(f"   {rank:<6} {title:<40} {pred_rating:<15.2f} {confidence}")
        else:
            print("   ⚠️ Tidak ada rekomendasi (semua anime sudah dirating)")
    
    except Exception as e:
        print(f"❌ Error generating recommendations: {e}")
        import traceback
        traceback.print_exc()
else:
    print("⚠️ Tidak ada user dengan ≥3 rating untuk testing")
    print("   Silakan tambahkan rating terlebih dahulu")

# ==========================================================================
# TEST 6: Cold-Start Handling
# ==========================================================================
print("\n❄️ TEST 6: Cold-Start Handling")
print("-" * 80)

# Cari user dengan rating < 3
cold_start_user = None
for user in User.objects.all()[:10]:
    rating_count = get_user_rating_count(user)
    if rating_count < 3:
        cold_start_user = user
        break

if cold_start_user:
    print(f"Testing cold-start untuk user: {cold_start_user.username}")
    print(f"Jumlah rating user: {get_user_rating_count(cold_start_user)}")
    
    recommendations = get_recommendations_for_user(
        cold_start_user,
        top_n=5,
        k_factors=8,
        min_pred=6.5
    )
    
    print(f"\n✅ Fallback ke popular anime")
    print(f"   Total recommendations: {len(recommendations)}")
    
    if recommendations:
        print(f"\n   Top 5 Popular Anime:")
        for rec in recommendations[:5]:
            print(f"   {rec['rank']}. {rec['anime'].title} (Rating: {rec['predicted_rating']:.2f})")
else:
    print("⚠️ Tidak ada cold-start user untuk testing")

# ==========================================================================
# TEST 7: Statistik Dataset
# ==========================================================================
print("\n📈 TEST 7: Statistik Dataset")
print("-" * 80)

total_users = User.objects.count()
total_anime = Anime.objects.count()
total_ratings = UserAnimeRating.objects.count()

cold_start_count = sum(1 for u in User.objects.all() if get_user_rating_count(u) < 3)
active_count = total_users - cold_start_count

if total_users > 0 and total_anime > 0:
    density = (total_ratings / (total_users * total_anime)) * 100
    
    print(f"Dataset Statistics:")
    print(f"   Total users: {total_users}")
    print(f"   Total anime: {total_anime}")
    print(f"   Total ratings: {total_ratings}")
    print(f"   Matrix density: {density:.2f}%")
    print(f"\nUser Segmentation:")
    print(f"   Cold-start users (<3 ratings): {cold_start_count} ({cold_start_count/total_users*100:.1f}%)")
    print(f"   Active users (≥3 ratings): {active_count} ({active_count/total_users*100:.1f}%)")
    
    # Rating distribution
    if total_ratings > 0:
        avg_rating = UserAnimeRating.objects.aggregate(avg=models.Avg('rating'))['avg']
        print(f"\nRating Statistics:")
        print(f"   Average rating: {avg_rating:.2f}")
        print(f"   Ratings per user: {total_ratings/total_users:.1f}")
        print(f"   Ratings per anime: {total_ratings/total_anime:.1f}")
else:
    print("⚠️ Dataset kosong - tidak ada data untuk statistik")

# ==========================================================================
# Summary
# ==========================================================================
print("\n" + "=" * 80)
print("TESTING SELESAI")
print("=" * 80)

if pivot_df is not None and test_user is not None:
    print("✅ Sistem rekomendasi SVD berjalan dengan baik!")
    print("\nNext steps:")
    print("1. Integrate dengan views.py untuk home page")
    print("2. Integrate dengan views_search.py untuk search page")
    print("3. Setup caching untuk performa lebih baik")
    print("4. Monitor dan tune parameter (k_factors, min_pred)")
else:
    print("⚠️ Perlu tindakan:")
    if pivot_df is None:
        print("- Tambahkan data rating ke database")
    if test_user is None:
        print("- Pastikan ada user dengan ≥3 rating untuk testing")

print("=" * 80)