from django.urls import path
from .views.auth import RegisterUserView, SendOTPView, VerifyOTPView
from .views.profile import UserProfileView

app_name = "accounts"

urlpatterns = [
    path("register/", RegisterUserView.as_view(), name="register"),
    path("send-otp/", SendOTPView.as_view(), name="send-otp"),
    path("verify-otp/", VerifyOTPView.as_view(), name="verify-otp"),
    path("profile/", UserProfileView.as_view(), name="profile"),
]