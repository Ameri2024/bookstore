from django.contrib import admin
from .models import Category, Author, Publisher, Book, BookVariant, Pack, PackItem, Review

admin.site.register(Category)
admin.site.register(Author)
admin.site.register(Publisher)


class BookVariantInline(admin.TabularInline):
    model = BookVariant
    extra = 1


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'average_rating']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [BookVariantInline]


class PackItemInline(admin.TabularInline):
    model = PackItem
    extra = 1


@admin.register(Pack)
class PackAdmin(admin.ModelAdmin):
    list_display = ['name', 'discount_percent', 'final_price', 'is_active']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [PackItemInline]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'content_object', 'rating', 'is_approved']
    list_editable = ['is_approved']