from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter
from .models import Book, Category, Author, Pack, Review
from .serializers import (
    BookSerializer, BookVariantSerializer, CategorySerializer,
    AuthorSerializer, PackSerializer, ReviewSerializer
)
from .filters import BookFilter


@extend_schema(
    tags=['Books'],
    summary='List books with filtering and search',
    parameters=[
        OpenApiParameter(name='category', description='Category ID', type=int),
        OpenApiParameter(name='min_price', description='Minimum price', type=int),
        OpenApiParameter(name='max_price', description='Maximum price', type=int),
        OpenApiParameter(name='search', description='Search in title, description, ISBN', type=str),
        OpenApiParameter(name='ordering', description='Ordering (price, -price, created_at)', type=str),
    ]
)
class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = BookFilter
    search_fields = ['title', 'description', 'isbn', 'publisher__name']
    ordering_fields = ['price', 'created_at', 'year_published']
    ordering = ['-created_at']

    @action(detail=True, methods=['get'])
    def variants(self, request, pk=None):
        book = self.get_object()
        variants = book.variants.filter(is_active=True)
        serializer = BookVariantSerializer(variants, many=True)
        return Response(serializer.data)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class PackViewSet(viewsets.ModelViewSet):
    queryset = Pack.objects.filter(is_active=True)
    serializer_class = PackSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    search_fields = ['name', 'description']


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        content_type = self.request.query_params.get('content_type')
        object_id = self.request.query_params.get('object_id')
        if content_type and object_id:
            from django.contrib.contenttypes.models import ContentType
            ct = ContentType.objects.get(model=content_type.lower())
            return Review.objects.filter(content_type=ct, object_id=object_id, is_approved=True)
        return Review.objects.filter(is_approved=True)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)