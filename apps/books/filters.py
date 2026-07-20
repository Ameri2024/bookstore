from django_filters import rest_framework as filters
from .models import Book


class BookFilter(filters.FilterSet):
    min_price = filters.NumberFilter(field_name='variants__price', lookup_expr='gte')
    max_price = filters.NumberFilter(field_name='variants__price', lookup_expr='lte')
    category_slug = filters.CharFilter(field_name='category__slug', lookup_expr='icontains')
    author_name = filters.CharFilter(field_name='authors__first_name', lookup_expr='icontains')
    in_stock = filters.BooleanFilter(method='filter_has_stock')

    def filter_has_stock(self, queryset, name, value):
        if value:
            return queryset.filter(variants__stock__gt=0).distinct()
        return queryset

    class Meta:
        model = Book
        fields = {
            'category': ['exact'],
            'year_published': ['exact', 'gte', 'lte'],
            'translator': ['icontains'],
        }