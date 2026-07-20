from django.urls import path
from .views import (
    BookViewSet, CategoryViewSet, AuthorViewSet,
    PackViewSet, ReviewViewSet
)

app_name = "books"

urlpatterns = [
    # Books
    path("books/", BookViewSet.as_view({"get": "list", "post": "create"}), name="book-list"),
    path("books/<int:pk>/", BookViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}), name="book-detail"),
    path("books/<int:pk>/variants/", BookViewSet.as_view({"get": "variants"}), name="book-variants"),

    # Categories
    path("categories/", CategoryViewSet.as_view({"get": "list", "post": "create"}), name="category-list"),
    path("categories/<int:pk>/", CategoryViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}), name="category-detail"),

    # Authors
    path("authors/", AuthorViewSet.as_view({"get": "list", "post": "create"}), name="author-list"),
    path("authors/<int:pk>/", AuthorViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}), name="author-detail"),

    # Packs
    path("packs/", PackViewSet.as_view({"get": "list", "post": "create"}), name="pack-list"),
    path("packs/<int:pk>/", PackViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}), name="pack-detail"),

    # Reviews
    path("reviews/", ReviewViewSet.as_view({"get": "list", "post": "create"}), name="review-list"),
    path("reviews/<int:pk>/", ReviewViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}), name="review-detail"),
]