from datetime import timedelta
import secrets
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from .managers import CustomUserManager


class CustomUser(AbstractUser):
    """
    Custom user model that uses a phone number as the primary identifier.
    """
    phone_number = models.CharField(
        max_length=11,
        unique=True,
        db_index=True,
        verbose_name="Phone Number",
        help_text="Enter the user's mobile phone number.",
    )
    address = models.TextField(blank=True, verbose_name="Address")
    postal_code = models.CharField(max_length=10, blank=True, verbose_name="Postal Code")
    first_name = models.CharField(max_length=150, blank=True, verbose_name="First Name")
    last_name = models.CharField(max_length=150, blank=True, verbose_name="Last Name")
    email = models.EmailField(blank=True, verbose_name="Email Address")

    username = None
    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = []
    objects = CustomUserManager()

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        full_name = f"{self.first_name} {self.last_name}".strip()
        return f"{full_name} ({self.phone_number})" if full_name else self.phone_number


class OTPCodeQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_used=False, expires_at__gt=timezone.now())


class OTPCode(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="otp_codes",
        verbose_name="User",
    )
    code = models.CharField(
        max_length=6,
        db_index=True,
        verbose_name="OTP Code",
        help_text="Six-digit one-time password.",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    expires_at = models.DateTimeField(verbose_name="Expires At")
    used_at = models.DateTimeField(null=True, blank=True, verbose_name="Used At")
    is_used = models.BooleanField(default=False, verbose_name="Used")
    failed_attempts = models.PositiveSmallIntegerField(default=0, verbose_name="Failed Attempts")
    objects = OTPCodeQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "One-Time Password"
        verbose_name_plural = "One-Time Passwords"
        indexes = [
            models.Index(fields=["user", "code"]),
            models.Index(fields=["expires_at"]),
        ]

    def save(self, *args, **kwargs):
        if self.expires_at is None:
            self.expires_at = timezone.now() + timedelta(minutes=2)
        super().save(*args, **kwargs)

    def mark_as_used(self):
        self.is_used = True
        self.used_at = timezone.now()
        self.save(update_fields=["is_used", "used_at"])

    def is_valid(self):
        return not self.is_used and self.expires_at > timezone.now() and self.failed_attempts < 5

    def increase_failed_attempts(self):
        self.failed_attempts += 1
        self.save(update_fields=["failed_attempts"])

    @staticmethod
    def generate_code():
        return str(secrets.randbelow(900000) + 100000)

    def __str__(self):
        status = "Used" if self.is_used else "Active"
        return f"{self.user.phone_number} ({status})"