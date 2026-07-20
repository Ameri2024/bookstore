from rest_framework import serializers
from .models import Cart, CartItem, Order, OrderItem
from apps.books.serializers import BookVariantSerializer, PackSerializer


class CartItemSerializer(serializers.ModelSerializer):
    book_variant_detail = BookVariantSerializer(source='book_variant', read_only=True)
    pack_detail = PackSerializer(source='pack', read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'book_variant', 'book_variant_detail', 'pack', 'pack_detail', 'quantity', 'total_price']

    def get_total_price(self, obj):
        return obj.get_total_price()


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()
    total_items = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'items', 'total_price', 'total_items']

    def get_total_price(self, obj):
        return obj.get_total_price()

    def get_total_items(self, obj):
        return obj.get_total_items()


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = '__all__'


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['user', 'session_key', 'total_price', 'final_amount', 'is_paid', 'paid_at', 'created_at']