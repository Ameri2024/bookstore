from django.urls import path
from .views import initiate_payment, payment_callback

app_name = "payments"

urlpatterns = [
    path("initiate/<int:order_id>/", initiate_payment, name="initiate_payment"),
    path("callback/", payment_callback, name="payment_callback"),
]