from django.contrib import admin
from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'order', 'amount', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['order__id', 'user__phone_number', 'authority', 'ref_id']
    readonly_fields = ['authority', 'ref_id']