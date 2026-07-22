from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from azbankgateways.urls import az_bank_gateways_urls
bank_urls = az_bank_gateways_urls()

schema_view = get_schema_view(
    openapi.Info(
        title="Bookstore API - mysite.com",
        default_version='v1',
        description="API documentation for the Bookstore project",
        terms_of_service="https://www.mysite.com/terms/",
        contact=openapi.Contact(email="info@mysite.ir"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # Authentication
    path('api/auth/', include('apps.accounts.urls')),

    # Books, categories, authors, packs, reviews
    path('api/', include('apps.books.urls')),

    # Cart and orders
    path('api/', include('apps.cart.urls')),

    # Payments
    path('api/payment/', include('apps.payments.urls')),

    # Banking gateway (azbankgateways) – correct usage
    path('bankgateways/', include(bank_urls[0])),  # Extract only the urlpatterns list

    # Swagger/ReDoc
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
