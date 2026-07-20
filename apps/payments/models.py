from django.db import models
from django.conf import settings
from apps.cart.models import Order  # Correct import for the Order model


class Transaction(models.Model):
    """
    Represents a payment transaction made through the banking gateway.
    Status choices: INIT (initiated), SUCCESS (paid), FAIL (failed).
    """
    STATUS_CHOICES = [
        ('INIT', 'Initiated'),
        ('SUCCESS', 'Successful'),
        ('FAIL', 'Failed'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,          # Use the configured user model
        on_delete=models.CASCADE,
        verbose_name="User"
    )
    order = models.ForeignKey(
        Order,                             # Imported from apps.cart.models
        on_delete=models.CASCADE,
        verbose_name="Order"
    )
    amount = models.PositiveIntegerField(
        help_text="Amount in IRR (Toman)"
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='INIT',
        verbose_name="Status"
    )
    authority = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Authority code from the gateway",
        verbose_name="Authority Code"
    )
    ref_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Reference ID returned by the gateway",
        verbose_name="Reference ID"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Payment Transaction"
        verbose_name_plural = "Payment Transactions"

    def __str__(self):
        return f"Transaction #{self.id} - {self.status} - Order #{self.order.id}"