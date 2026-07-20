from rest_framework import serializers
from .models import Category, Author, Publisher, Book, BookVariant, Pack, PackItem, Review


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = '__all__'


class PublisherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Publisher
        fields = '__all__'


class BookVariantSerializer(serializers.ModelSerializer):
    final_price = serializers.ReadOnlyField()
    has_discount = serializers.ReadOnlyField()

    class Meta:
        model = BookVariant
        fields = ['id', 'size', 'binding', 'price', 'sale_price', 'final_price', 'has_discount', 'stock', 'sku', 'is_active']


class BookSerializer(serializers.ModelSerializer):
    variants = BookVariantSerializer(many=True, read_only=True)
    average_rating = serializers.FloatField(read_only=True)

    class Meta:
        model = Book
        fields = '__all__'


class PackItemSerializer(serializers.ModelSerializer):
    book_variant_detail = BookVariantSerializer(source='book_variant', read_only=True)

    class Meta:
        model = PackItem
        fields = ['id', 'book_variant', 'book_variant_detail', 'quantity']


class PackSerializer(serializers.ModelSerializer):
    items = PackItemSerializer(many=True, read_only=True)
    base_price = serializers.ReadOnlyField()
    final_price = serializers.ReadOnlyField()
    average_rating = serializers.FloatField(read_only=True)

    class Meta:
        model = Pack
        fields = '__all__'


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'user', 'rating', 'comment', 'is_approved', 'created_at']
        read_only_fields = ['user', 'is_approved', 'created_at']