from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.utils.timesince import timesince
from django.db.models import Count

from .models import Anime, AnimeComment, AnimeCommentLike


def _comment_to_dict(comment, request_user):
    # hitung likes + apakah user ini sudah like
    likes_count = getattr(comment, "likes_count", None)
    if likes_count is None:
        likes_count = comment.likes.count()

    liked = AnimeCommentLike.objects.filter(comment=comment, user=request_user).exists()

    return {
        "id": comment.id,
        "author": comment.user.username,
        "avatar": (comment.user.username[:1] or "U").upper(),
        "time": f"{timesince(comment.created_at)} ago",
        "text": comment.text,
        "likes": likes_count,
        "liked": liked,
    }


@login_required
@require_http_methods(["GET", "POST"])
def api_comments(request, anime_id: int):
    """
    GET  -> list komentar untuk anime
    POST -> tambah komentar untuk anime
    """
    try:
        anime = Anime.objects.get(id=anime_id)
    except Anime.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Anime not found"}, status=404)

    if request.method == "GET":
        qs = (
            AnimeComment.objects
            .filter(anime=anime)
            .select_related("user")
            .annotate(likes_count=Count("likes"))
            .order_by("-created_at")
        )
        data = [_comment_to_dict(c, request.user) for c in qs]
        return JsonResponse({"status": "success", "count": len(data), "data": data})

    # POST
    text = (request.POST.get("text") or "").strip()
    if not text:
        return JsonResponse({"status": "error", "message": "Comment text is required"}, status=400)

    # optional: batasi panjang
    if len(text) > 2000:
        return JsonResponse({"status": "error", "message": "Comment too long"}, status=400)

    c = AnimeComment.objects.create(anime=anime, user=request.user, text=text)
    return JsonResponse({"status": "success", "comment": _comment_to_dict(c, request.user)})


@login_required
@require_http_methods(["POST"])
def api_toggle_like(request, comment_id: int):
    """
    Toggle like pada komentar
    """
    try:
        c = AnimeComment.objects.select_related("anime").get(id=comment_id)
    except AnimeComment.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Comment not found"}, status=404)

    obj = AnimeCommentLike.objects.filter(comment=c, user=request.user).first()
    if obj:
        obj.delete()
        liked = False
    else:
        AnimeCommentLike.objects.create(comment=c, user=request.user)
        liked = True

    likes_count = AnimeCommentLike.objects.filter(comment=c).count()
    return JsonResponse({"status": "success", "liked": liked, "likes": likes_count})
