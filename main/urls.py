# main/urls.py
from django.urls import path
from . import views
from . import views_widgets
from . import views_comments
from . import views_search  # ✅ Tambahkan import untuk views_search

urlpatterns = [
    path("home/", views.home, name="home"),

    # ✅ SEARCH PAGE + API (pastikan menggunakan views_search)
    path("search/", views_search.search_page, name="search_page"),
    path("api/search/", views_search.api_search, name="api_search"),

    # ✅ WATCH PAGE
    path("watch/<int:anime_id>/", views.watch, name="watch"),

    # ✅ API submit rating
    path("api/rate/<int:anime_id>/", views.api_rate_anime, name="api_rate_anime"),

    # Widgets
    path("api/widgets/top-views/", views_widgets.api_top_views, name="api_top_views"),
    path("api/widgets/today/", views_widgets.api_today, name="api_today"),

    # ✅ Comments API
    path("api/anime/<int:anime_id>/comments/", views_comments.api_comments, name="api_comments"),
    path("api/comments/<int:comment_id>/like/", views_comments.api_toggle_like, name="api_comment_like"),
]