# apps/accounts/views.py
import logging
from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import OTPCode
from .serializers import (
    OTPVerifySerializer,
    OTPSendSerializer,
    UserProfileUpdateSerializer,
    UserRegisterSerializer,
    UserSerializer,
)
from .services import KavenegarSMS

User = get_user_model()
logger = logging.getLogger(__name__)



class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Retrieve and update the authenticated user's profile.
    """
    schema = None  # برای جلوگیری از خطای drf-spectacular
    serializer_class = UserProfileUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return UserSerializer
        return UserProfileUpdateSerializer


class RegisterUserView(generics.CreateAPIView):
    """
    Register a new user using a mobile phone number.
    """
    schema = None
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # تولید توکن برای کاربر تازه ثبت‌نام شده
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)


# ------------------------------------------------------------
# SendOTPView
# ------------------------------------------------------------
class SendOTPView(APIView):
    """
    دریافت شماره تلفن و ارسال کد تایید (OTP) از طریق کاوه‌نگار
    """
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        request_body=OTPSendSerializer,
        responses={200: 'کد ارسال شد', 500: 'خطا'}
    )

    def post(self, request):
        serializer = OTPSendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone_number = serializer.validated_data['phone_number']

        # ایجاد خودکار کاربر در صورت عدم وجود
        user, created = User.objects.get_or_create(
            phone_number=phone_number,
            defaults={
                'username': phone_number,
                'first_name': '',
                'last_name': '',
                'address': '',
                'postal_code': ''
            }
        )
        if created:
            user.set_unusable_password()
            user.save()
            logger.info(f"New user created with phone: {phone_number}")

        # تولید و ارسال کد ۶ رقمی
        otp_code = str(random.randint(100000, 999999))
        sms_service = KavenegarSMS()
        success = sms_service.send_verification_code(phone_number, otp_code, template="verify")

        if success:
            # ذخیره کد در session
            request.session['otp_code'] = otp_code
            request.session['otp_phone'] = phone_number
            request.session['otp_expiry'] = str(timezone.now() + timedelta(minutes=2))
            return Response({'message': 'کد تایید با موفقیت ارسال شد.'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'ارسال پیامک با مشکل مواجه شد. لطفاً مجدداً تلاش کنید.'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ------------------------------------------------------------
# VerifyOTPView
# ------------------------------------------------------------
class VerifyOTPView(APIView):
    """
    تایید کد OTP و ورود به حساب کاربری (دریافت توکن JWT)
    """
    schema = None
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone_number = serializer.validated_data['phone_number']
        code = serializer.validated_data['code']

        # بررسی کد ذخیره شده در session
        stored_code = request.session.get('otp_code')
        stored_phone = request.session.get('otp_phone')
        stored_expiry = request.session.get('otp_expiry')

        if not stored_code or not stored_phone or not stored_expiry:
            return Response({'error': 'کد تایید منقضی شده است. لطفاً مجدداً درخواست دهید.'},
                            status=status.HTTP_400_BAD_REQUEST)

        # بررسی انقضای کد
        if timezone.now() > datetime.fromisoformat(stored_expiry):
            return Response({'error': 'کد تایید منقضی شده است.'},
                            status=status.HTTP_400_BAD_REQUEST)

        if stored_code == code and stored_phone == phone_number:
            # حذف کد از session
            del request.session['otp_code']
            del request.session['otp_phone']
            del request.session['otp_expiry']

            try:
                user = User.objects.get(phone_number=phone_number)
            except User.DoesNotExist:
                return Response({'error': 'کاربری با این شماره تلفن یافت نشد.'},
                                status=status.HTTP_404_NOT_FOUND)

            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'کد وارد شده صحیح نیست.'},
                            status=status.HTTP_400_BAD_REQUEST)