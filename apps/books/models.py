from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, allow_unicode=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


class Author(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    bio = models.TextField(blank=True)
    slug = models.SlugField(unique=True, allow_unicode=True)
    photo = models.ImageField(upload_to='authors/', blank=True, null=True)

    class Meta:
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Publisher(models.Model):
    name = models.CharField(max_length=150)
    slug = models.SlugField(unique=True)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=250)
    slug = models.SlugField(unique=True, allow_unicode=True)
    subtitle = models.CharField(max_length=300, blank=True)
    description = models.TextField()
    isbn = models.CharField(max_length=13, unique=True, blank=True, null=True)
    pages = models.PositiveIntegerField(default=0)
    year_published = models.IntegerField(null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    authors = models.ManyToManyField(Author, related_name='books')
    publisher = models.ForeignKey(Publisher, on_delete=models.SET_NULL, null=True)
    translator = models.CharField(max_length=200, blank=True)
    cover_image = models.ImageField(upload_to='book_covers/', blank=True)
    average_rating = models.FloatField(default=0.0)
    views_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    reviews = GenericRelation('Review', related_query_name='book')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def update_average_rating(self):
        approved = self.reviews.filter(is_approved=True)
        if approved.exists():
            avg = approved.aggregate(models.Avg('rating'))['rating__avg']
            self.average_rating = round(avg, 1)
        else:
            self.average_rating = 0.0
        self.save(update_fields=['average_rating'])


class BookVariant(models.Model):
    # Size choices in English (you can keep Persian if needed)
    BOOK_SIZE_CHOICES = [
        ('standard', 'Standard'),
        ('pocket', 'Pocket'),
        ('large', 'Large'),
        ('folio', 'Folio'),
        ('mini', 'Mini'),
    ]
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='variants')
    size = models.CharField(max_length=20, choices=BOOK_SIZE_CHOICES, default='standard')
    binding = models.CharField(max_length=50, blank=True, help_text="Hardcover / Paperback")
    price = models.DecimalField(max_digits=10, decimal_places=0)
    sale_price = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)
    sale_start_date = models.DateTimeField(null=True, blank=True, help_text="Start of discount period")
    sale_end_date = models.DateTimeField(null=True, blank=True, help_text="End of discount period")
    stock = models.PositiveIntegerField(default=0)
    sku = models.CharField(max_length=100, unique=True, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('book', 'size', 'binding')
        ordering = ['book__title', 'size']

    def __str__(self):
        return f"{self.book.title} - {self.get_size_display()}"

    @property
    def final_price(self):
        if self.sale_price is not None:
            now = timezone.now()
            if self.sale_start_date and self.sale_end_date:
                if self.sale_start_date <= now <= self.sale_end_date:
                    return self.sale_price
            elif not self.sale_start_date and not self.sale_end_date:
                return self.sale_price
        return self.price

    @property
    def has_discount(self):
        return self.final_price < self.price

    def check_stock(self, quantity):
        return self.stock >= quantity

    def decrease_stock(self, quantity):
        if self.check_stock(quantity):
            self.stock -= quantity
            self.save()
            return True
        return False


class Pack(models.Model):
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(unique=True, allow_unicode=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='packs/', blank=True, null=True)
    discount_percent = models.PositiveIntegerField(default=0, validators=[MaxValueValidator(100)])
    is_active = models.BooleanField(default=True)
    average_rating = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    reviews = GenericRelation('Review', related_query_name='pack')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def base_price(self):
        return sum(item.book_variant.final_price * item.quantity for item in self.items.all())

    @property
    def final_price(self):
        return self.base_price * (100 - self.discount_percent) // 100

    def check_stock_for_pack(self):
        return all(item.book_variant.stock >= item.quantity for item in self.items.all())

    def decrease_stock_for_pack(self):
        for item in self.items.all():
            if not item.book_variant.decrease_stock(item.quantity):
                return False
        return True

    def update_average_rating(self):
        approved = self.reviews.filter(is_approved=True)
        if approved.exists():
            avg = approved.aggregate(models.Avg('rating'))['rating__avg']
            self.average_rating = round(avg, 1)
        else:
            self.average_rating = 0.0
        self.save(update_fields=['average_rating'])


class PackItem(models.Model):
    pack = models.ForeignKey(Pack, on_delete=models.CASCADE, related_name='items')
    book_variant = models.ForeignKey(BookVariant, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('pack', 'book_variant')

    def __str__(self):
        return f"{self.pack.name}: {self.quantity} x {self.book_variant}"


class Review(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES, validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        unique_together = ('user', 'content_type', 'object_id')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} - {self.content_object} - {self.rating}⭐"


from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver(post_save, sender=Review)
@receiver(post_delete, sender=Review)
def update_rating_on_review_change(sender, instance, **kwargs):
    obj = instance.content_object
    if hasattr(obj, 'update_average_rating'):
        obj.update_average_rating()