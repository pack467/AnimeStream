from django.conf import settings
from django.db import models


class Anime(models.Model):
    title = models.CharField(max_length=255, unique=True)
    title_clean = models.CharField(max_length=255, db_index=True)

    genre = models.CharField(max_length=255, blank=True)
    total_episode = models.CharField(max_length=50, blank=True)  # bisa angka / TBA
    anime_type = models.CharField(max_length=30, blank=True)     # TV/Movie/OVA/ONA/Special
    year_release = models.CharField(max_length=10, blank=True)
    content_rating = models.CharField(max_length=30, blank=True)
    status = models.CharField(max_length=50, blank=True)

    total_rating = models.FloatField(default=0.0)  # global rating (1-10)
    cover = models.CharField(max_length=255, blank=True)         # nama file jpg
    wallpaper = models.CharField(max_length=255, blank=True)     # nama file jpg

    def __str__(self):
        return self.title


class UserAnimeRating(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    anime = models.ForeignKey(Anime, on_delete=models.CASCADE)
    rating = models.FloatField()  # 1.0 - 10.0
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "anime")

    def __str__(self):
        return f"{self.user.username} - {self.anime.title} ({self.rating})"


# ✅ untuk Top Views
class AnimeViewLog(models.Model):
    anime = models.ForeignKey(Anime, on_delete=models.CASCADE, related_name="view_logs")
    viewed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.anime.title} - {self.viewed_at}"


# ✅ untuk Today (episode terbaru)
class EpisodeRelease(models.Model):
    anime = models.ForeignKey(Anime, on_delete=models.CASCADE, related_name="episodes")
    episode = models.CharField(max_length=50)  # contoh: "Episode 12"
    released_at = models.DateTimeField(db_index=True)

    class Meta:
        ordering = ["-released_at"]

    def __str__(self):
        return f"{self.anime.title} - {self.episode}"


# ✅ Komentar untuk Watch page
class AnimeComment(models.Model):
    anime = models.ForeignKey(Anime, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="anime_comments")
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.anime.title} - {self.user.username}"


# ✅ Like komentar (opsional, untuk tombol 👍)
class AnimeCommentLike(models.Model):
    comment = models.ForeignKey(AnimeComment, on_delete=models.CASCADE, related_name="likes")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comment_likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("comment", "user")

    def __str__(self):
        return f"{self.user.username} likes #{self.comment.id}"