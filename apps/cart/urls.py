from django.urls import path
from .views import CartViewSet, OrderViewSet

app_name = "cart"

urlpatterns = [
    # Cart endpoints
    path("cart/", CartViewSet.as_view({"get": "retrieve"}), name="cart-detail"),
    path("cart/add_item/", CartViewSet.as_view({"post": "add_item"}), name="cart-add-item"),
    path("cart/remove_item/", CartViewSet.as_view({"post": "remove_item"}), name="cart-remove-item"),
    path("cart/update_quantity/", CartViewSet.as_view({"post": "update_quantity"}), name="cart-update-quantity"),
    path("cart/clear_cart/", CartViewSet.as_view({"post": "clear_cart"}), name="cart-clear"),

    # Order endpoints
    path("orders/", OrderViewSet.as_view({"get": "list", "post": "create"}), name="order-list"),
    path("orders/<int:pk>/", OrderViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}), name="order-detail"),
]