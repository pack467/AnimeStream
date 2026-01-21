from django.contrib import admin
from .models import Anime, UserAnimeRating, AnimeViewLog, EpisodeRelease, AnimeComment, AnimeCommentLike

@admin.register(Anime)
class AnimeAdmin(admin.ModelAdmin):
    list_display = ("title", "anime_type", "year_release", "total_rating", "status")
    search_fields = ("title", "genre", "title_clean")
    list_filter = ("anime_type", "status", "content_rating")
    list_per_page = 20

@admin.register(UserAnimeRating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ("user", "anime", "rating", "created_at")
    search_fields = ("user__username", "anime__title")
    list_filter = ("rating", "created_at")
    list_per_page = 20

@admin.register(AnimeViewLog)
class AnimeViewLogAdmin(admin.ModelAdmin):
    list_display = ("anime", "viewed_at")
    search_fields = ("anime__title",)
    list_filter = ("viewed_at",)
    list_per_page = 20

@admin.register(EpisodeRelease)
class EpisodeReleaseAdmin(admin.ModelAdmin):
    list_display = ("anime", "episode", "released_at")
    search_fields = ("anime__title", "episode")
    list_filter = ("released_at",)
    list_per_page = 20

@admin.register(AnimeComment)
class AnimeCommentAdmin(admin.ModelAdmin):
    list_display = ("user", "anime", "text_preview", "likes_count", "created_at")
    search_fields = ("user__username", "anime__title", "text")
    list_filter = ("created_at", "anime")
    list_per_page = 20
    
    def text_preview(self, obj):
        return obj.text[:50] + "..." if len(obj.text) > 50 else obj.text
    text_preview.short_description = "Text"
    
    def likes_count(self, obj):
        return obj.likes.count()
    likes_count.short_description = "Likes"

@admin.register(AnimeCommentLike)
class AnimeCommentLikeAdmin(admin.ModelAdmin):
    list_display = ("user", "comment", "created_at")
    search_fields = ("user__username", "comment__text")
    list_filter = ("created_at",)
    list_per_page = 20