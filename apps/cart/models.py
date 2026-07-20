from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from apps.books.models import BookVariant, Pack


class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_total_price(self):
        return sum(item.get_total_price() for item in self.items.all())

    def get_total_items(self):
        return sum(item.quantity for item in self.items.all())

    def __str__(self):
        if self.user:
            return f"Cart of {self.user.username}"
        return f"Cart (session: {self.session_key})"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    book_variant = models.ForeignKey(BookVariant, on_delete=models.CASCADE, null=True, blank=True)
    pack = models.ForeignKey(Pack, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(book_variant__isnull=False, pack__isnull=True) |
                    models.Q(book_variant__isnull=True, pack__isnull=False)
                ),
                name="cart_item_one_type_only"
            )
        ]

    def clean(self):
        if self.book_variant and self.pack:
            raise ValidationError("An item cannot be both a book and a pack.")
        if not self.book_variant and not self.pack:
            raise ValidationError("An item must be either a book or a pack.")

    def get_total_price(self):
        if self.book_variant:
            return self.book_variant.final_price * self.quantity
        elif self.pack:
            return self.pack.final_price * self.quantity
        return 0

    def __str__(self):
        if self.book_variant:
            return f"{self.book_variant} x {self.quantity}"
        return f"{self.pack.name} x {self.quantity}"


class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    session_key = models.CharField(max_length=40, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    province = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    address = models.TextField()
    postal_code = models.CharField(max_length=10)
    total_price = models.DecimalField(max_digits=12, decimal_places=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    final_amount = models.DecimalField(max_digits=12, decimal_places=0)
    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - {self.full_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product_type = models.CharField(max_length=20)  # 'book' or 'pack'
    product_name = models.CharField(max_length=250)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=0)
    total_price = models.DecimalField(max_digits=12, decimal_places=0)
    book_variant_id = models.PositiveIntegerField(null=True, blank=True)
    pack_id = models.PositiveIntegerField(null=True, blank=True)
    pack_snapshot = models.JSONField(default=dict, blank=True, help_text="Details of pack items at purchase time")

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"