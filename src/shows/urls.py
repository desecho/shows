"""URL Configuration."""

from django.conf.urls import include
from django.contrib import admin
from django.urls import path
from django.views.defaults import page_not_found
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from showsapp.types import URL
from showsapp.views.health import HealthView
from showsapp.views.list import (
    AddToListView,
    ChangeRatingView,
    RecordsView,
    RemoveRecordView,
    SaveCommentView,
    SaveRecordsOrderView,
    ShareToSocialMediaView,
)
from showsapp.views.recommendations import RecommendationsView
from showsapp.views.search import AddToListFromDbView, SearchShowView
from showsapp.views.show import ShowDetailView
from showsapp.views.stats import StatsView
from showsapp.views.trending import TrendingView
from showsapp.views.user import UserCheckEmailAvailabilityView, UserPreferencesView

admin.autodiscover()


def path_404(url_path: str, name: str) -> URL:
    """Return a path for 404."""
    return path(
        url_path,
        page_not_found,
        name=name,
        kwargs={"exception": Exception("Page not Found")},
    )


urlpatterns: list[URL] = [
    # Health
    path("health/", HealthView.as_view()),
    # Admin
    path("admin/", admin.site.urls),
    # Auth
    path("token/", TokenObtainPairView.as_view()),
    path("token/refresh/", TokenRefreshView.as_view()),
    # User
    path("user/", include("rest_registration.api.urls")),
    path("user/preferences/", UserPreferencesView.as_view()),
    path("user/check-email-availability/", UserCheckEmailAvailabilityView.as_view()),
    path("show/<int:tmdb_id>/", ShowDetailView.as_view(), name="show_detail"),
    path("search/", SearchShowView.as_view()),
    path("trending/", TrendingView.as_view(), name="trending"),
    path("recommendations/", RecommendationsView.as_view(), name="recommendations"),
    path("stats/", StatsView.as_view(), name="stats"),
    path("add-to-list-from-db/", AddToListFromDbView.as_view()),
    # List
    path("records/", RecordsView.as_view()),
    path("users/<str:username>/records/", RecordsView.as_view()),
    path_404("remove-record/", "remove_record"),
    path("remove-record/<int:record_id>/", RemoveRecordView.as_view()),
    path("save-records-order/", SaveRecordsOrderView.as_view()),
    path_404("add-to-list/", "add_to_list"),
    path("add-to-list/<int:show_id>/", AddToListView.as_view()),
    path_404("change-rating/", "change_rating"),
    path("change-rating/<int:record_id>/", ChangeRatingView.as_view()),
    path_404("save-comment/", "save_comment"),
    path("save-comment/<int:record_id>/", SaveCommentView.as_view()),
    path_404("share/", "share"),
    path("share/<int:record_id>/", ShareToSocialMediaView.as_view()),
]
