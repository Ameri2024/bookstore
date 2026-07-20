from django.contrib import admin
from .models import Cart, CartItem, Order, OrderItem

admin.site.register(Cart)
admin.site.register(CartItem)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'full_name', 'final_amount', 'status', 'is_paid', 'created_at']
    list_editable = ['status']
    inlines = [OrderItemInline]