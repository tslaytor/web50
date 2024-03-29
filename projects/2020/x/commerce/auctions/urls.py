from unicodedata import name
from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("create_listing", views.create, name="create"),
    path("listing/<int:listing_id>", views.listing, name="listing"),
    path("watchlist", views.watchlist, name="watchlist"),
    path("remove_from_watchlist", views.remove_from_watchlist, name="remove_from_watchlist"),
    path("bid", views.bid, name="bid"),
    path("close_listing", views.close_listing, name=("close")),
    path("deactivated", views.deactivated, name="deactivated"),
    path("comment", views.comment, name="comment"),
    path("categories", views.categories, name="categories"),
    path("category_filter/<int:cat_id>", views.category_filter, name='category_filter')
]
