# main/views_search.py
"""
Search Views dengan dukungan:
1. Normal Search (text, filters, sorting)
2. SVD Recommendations Mode (sort=recommended)
3. Age-Match Mode (sort=age-match)
"""

from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
import logging

from .models import Anime
from .recommender import get_recommendations_for_user

logger = logging.getLogger(__name__)


@login_required
def search_page(request):
    """Render halaman search utama"""
    return render(request, "pages/search.html")


def _split_csv_param(request, key: str):
    """Helper untuk split CSV parameter dari query string"""
    raw = (request.GET.get(key) or "").strip()
    if not raw:
        return []
    return [x.strip() for x in raw.split(",") if x.strip()]


def _age_to_db_q(age_values):
    """
    Convert age rating values dari frontend ke database Q query
    
    HTML values: All Ages, PG-13, R-17, R-18
    DB examples:
      "G - All Ages"
      "PG-13 - Teens 13 or older"
      "R - 17+ (violence & profanity)"
      "R+ - Mild Nudity"
    """
    q = Q()
    for v in age_values:
        v = (v or "").strip()

        if v.lower() == "all ages":
            q |= Q(content_rating__icontains="All Ages") | Q(content_rating__startswith="G")
        elif v.upper() == "PG-13":
            q |= Q(content_rating__icontains="PG-13")
        elif v.upper() in ("R-17", "R17", "17+"):
            q |= Q(content_rating__icontains="R - 17") | Q(content_rating__startswith="R -")
        elif v.upper() in ("R-18", "R18", "18+"):
            q |= Q(content_rating__icontains="R+")
        else:
            q |= Q(content_rating__icontains=v)

    return q


def _check_genre_token(genre_str: str, selected_genres):
    """
    Cek apakah genre_str mengandung genre yang dipilih (token-accurate)
    
    genre_str contoh: "Action, Adventure, Fantasy"
    selected_genres: ["Fantasy", "Drama"]
    -> TRUE kalau ada token genre yang match exact (case-insensitive)
    """
    if not selected_genres:
        return True
    if not genre_str:
        return False

    tokens = [g.strip().lower() for g in genre_str.split(",") if g.strip()]
    wanted = [g.strip().lower() for g in selected_genres if g.strip()]
    return any(w in tokens for w in wanted)


def _cover_url(a: Anime):
    """Helper untuk generate cover URL"""
    cover = a.cover
    if cover and not str(cover).startswith("http") and "/" not in str(cover):
        return f"/static/images/cover/{cover}"
    return cover or ""


def _get_user_age_preference(user):
    """
    Helper untuk mendapatkan preferensi usia user
    
    TODO: Implementasikan berdasarkan user profile
    Return: string seperti "PG-13", "R-17+", "All Ages", dsb
    """
    if hasattr(user, 'profile') and hasattr(user.profile, 'age_preference'):
        return user.profile.age_preference
    return "PG-13"  # Default untuk remaja


@login_required
def api_search(request):
    """
    API endpoint untuk pencarian anime dengan filter
    
    Modes:
    1. sort=recommended → SVD collaborative filtering
    2. sort=age-match → Filter berdasarkan usia user + rating tertinggi
    3. default → Normal search dengan filters dan sorting
    
    Parameters:
    - q: Search query (title/genre)
    - page: Page number
    - per_page: Items per page
    - sort: recommended | age-match | popular | newest | rating | title
    - min_rating: Minimum rating filter
    - genres: Comma-separated genre list
    - years: Comma-separated year list
    - status: Comma-separated status list
    - type: Comma-separated type list
    - age_ratings: Comma-separated age rating list
    """
    # Parse parameters
    q_text = (request.GET.get("q") or "").strip()
    page = int(request.GET.get("page") or 1)
    per_page = int(request.GET.get("per_page") or 12)
    sort = (request.GET.get("sort") or "popular").strip()
    min_rating = float(request.GET.get("min_rating") or 0)

    genres = _split_csv_param(request, "genres")
    years = _split_csv_param(request, "years")
    status = _split_csv_param(request, "status")
    types = _split_csv_param(request, "type")
    age_ratings = _split_csv_param(request, "age_ratings")

    logger.info(f"🔍 Search request - User: {request.user.username}, Sort: {sort}, Query: '{q_text}'")

    # ==============================
    # MODE 1: SVD RECOMMENDED
    # ==============================
    if sort == "recommended" and request.user.is_authenticated:
        logger.info(f"📊 Using SVD recommendations mode")
        
        try:
            # Dapatkan rekomendasi SVD (1000 items)
            rec = get_recommendations_for_user(
                request.user,
                top_n=1000,
                k_factors=8,
                min_pred=6.5
            )
            
            logger.info(f"✅ Got {len(rec)} SVD recommendations")

            # Apply filters pada hasil rekomendasi
            items = []
            for r in rec:
                a = r["anime"]

                # Min rating filter (gunakan total_rating)
                if float(a.total_rating or 0) < min_rating:
                    continue

                # Text search filter
                if q_text:
                    s = q_text.lower()
                    if (s not in (a.title or "").lower()) and (s not in (a.genre or "").lower()):
                        continue

                # Year filter
                if years and str(a.year_release or "").strip() not in years:
                    continue

                # Status filter
                if status and (a.status or "").strip() not in status:
                    continue

                # Type filter
                if types and (a.anime_type or "").strip() not in types:
                    continue

                # Age rating filter
                if age_ratings:
                    cr = (a.content_rating or "")
                    ok = False
                    low = cr.lower()
                    for v in age_ratings:
                        vv = v.lower()
                        if vv == "all ages" and ("all ages" in low or low.startswith("g")):
                            ok = True
                            break
                        if vv == "pg-13" and "pg-13" in low:
                            ok = True
                            break
                        if vv in ("r-17", "r17", "17+") and ("r - 17" in low or low.startswith("r -")):
                            ok = True
                            break
                        if vv in ("r-18", "r18", "18+") and "r+" in low:
                            ok = True
                            break
                    if not ok:
                        continue

                # Genre filter (token-accurate)
                if genres and not _check_genre_token(a.genre or "", genres):
                    continue

                items.append(a)

            # Pagination
            paginator = Paginator(items, per_page)
            p = paginator.get_page(page)

            # Build results
            results = []
            for a in p.object_list:
                g_list = [x.strip() for x in (a.genre or "").split(",") if x.strip()]
                results.append({
                    "id": a.id,
                    "title": a.title,
                    "year": a.year_release,
                    "episodes": a.total_episode,
                    "rating": round(float(a.total_rating or 0), 2),
                    "genres": g_list,
                    "cover": _cover_url(a),
                })

            logger.info(f"✅ Returning {len(results)} filtered SVD recommendations (page {page}/{paginator.num_pages})")

            return JsonResponse({
                "page": page,
                "per_page": per_page,
                "total": paginator.count,
                "total_pages": paginator.num_pages,
                "results": results,
            })

        except Exception as e:
            logger.error(f"❌ Error in SVD recommendations: {e}", exc_info=True)
            # Fallback ke popular jika error
            sort = "popular"

    # ==============================
    # MODE 2: AGE-MATCH (SESUAI USIA)
    # ==============================
    if sort == "age-match" and request.user.is_authenticated:
        logger.info(f"👶 Using age-match mode")
        
        # Dapatkan preferensi usia user
        user_age_pref = _get_user_age_preference(request.user)
        logger.info(f"User age preference: {user_age_pref}")
        
        # Build queryset dengan filter normal
        qs = Anime.objects.all()

        if q_text:
            qs = qs.filter(
                Q(title__icontains=q_text) |
                Q(title_clean__icontains=q_text) |
                Q(genre__icontains=q_text)
            )

        if min_rating > 0:
            qs = qs.filter(total_rating__gte=min_rating)

        if years:
            qs = qs.filter(year_release__in=years)

        if status:
            qs = qs.filter(status__in=status)

        if types:
            qs = qs.filter(anime_type__in=types)

        if age_ratings:
            qs = qs.filter(_age_to_db_q(age_ratings))
        else:
            # Jika tidak ada filter usia, gunakan preferensi user
            qs = qs.filter(_age_to_db_q([user_age_pref]))

        # Genre filter
        if genres:
            gq = Q()
            for g in genres:
                if g.strip():
                    gq |= Q(genre__icontains=g.strip())
            qs = qs.filter(gq)
            qs_list = [a for a in qs if _check_genre_token(a.genre or "", genres)]
        else:
            qs_list = list(qs)

        # Sort berdasarkan rating (anime sesuai usia dengan rating tertinggi)
        qs_list.sort(key=lambda a: float(a.total_rating or 0), reverse=True)

        paginator = Paginator(qs_list, per_page)
        p = paginator.get_page(page)

        results = []
        for a in p.object_list:
            g_list = [x.strip() for x in (a.genre or "").split(",") if x.strip()]
            results.append({
                "id": a.id,
                "title": a.title,
                "year": a.year_release,
                "episodes": a.total_episode,
                "rating": round(float(a.total_rating or 0), 2),
                "genres": g_list,
                "cover": _cover_url(a),
            })

        logger.info(f"✅ Returning {len(results)} age-matched anime (page {page}/{paginator.num_pages})")

        return JsonResponse({
            "page": page,
            "per_page": per_page,
            "total": paginator.count,
            "total_pages": paginator.num_pages,
            "results": results,
        })

    # ==============================
    # MODE 3: NORMAL SEARCH (queryset)
    # ==============================
    logger.info(f"🔎 Using normal search mode with sort: {sort}")
    
    qs = Anime.objects.all()

    if q_text:
        qs = qs.filter(
            Q(title__icontains=q_text) |
            Q(title_clean__icontains=q_text) |
            Q(genre__icontains=q_text)
        )

    if min_rating > 0:
        qs = qs.filter(total_rating__gte=min_rating)

    if years:
        qs = qs.filter(year_release__in=years)

    if status:
        qs = qs.filter(status__in=status)

    if types:
        qs = qs.filter(anime_type__in=types)

    if age_ratings:
        qs = qs.filter(_age_to_db_q(age_ratings))

    # Genre filter (token-accurate)
    if genres:
        gq = Q()
        for g in genres:
            if g.strip():
                gq |= Q(genre__icontains=g.strip())
        qs = qs.filter(gq)
        qs_list = [a for a in qs if _check_genre_token(a.genre or "", genres)]
    else:
        qs_list = list(qs)

    # Sort
    if sort == "newest":
        qs_list.sort(key=lambda a: (str(a.year_release or ""), float(a.total_rating or 0)), reverse=True)
    elif sort == "rating":
        qs_list.sort(key=lambda a: float(a.total_rating or 0), reverse=True)
    elif sort == "title":
        qs_list.sort(key=lambda a: (a.title or "").lower())
    else:
        # popular default
        qs_list.sort(key=lambda a: float(a.total_rating or 0), reverse=True)

    paginator = Paginator(qs_list, per_page)
    p = paginator.get_page(page)

    results = []
    for a in p.object_list:
        g_list = [x.strip() for x in (a.genre or "").split(",") if x.strip()]
        results.append({
            "id": a.id,
            "title": a.title,
            "year": a.year_release,
            "episodes": a.total_episode,
            "rating": round(float(a.total_rating or 0), 2),
            "genres": g_list,
            "cover": _cover_url(a),
        })

    logger.info(f"✅ Returning {len(results)} search results (page {page}/{paginator.num_pages})")

    return JsonResponse({
        "page": page,
        "per_page": per_page,
        "total": paginator.count,
        "total_pages": paginator.num_pages,
        "results": results,
    })