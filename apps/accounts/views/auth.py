import logging
from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status, throttling
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiResponse
from ..models import OTPCode
from ..serializers import (
    OTPSendSerializer, OTPVerifySerializer,
    UserRegisterSerializer, UserSerializer,
)
from ..services import KavenegarService

logger = logging.getLogger(__name__)
User = get_user_model()


class OTPRequestThrottle(throttling.AnonRateThrottle):
    rate = "3/5min"


class RegisterUserView(generics.CreateAPIView):
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request=UserRegisterSerializer,
        responses={201: UserSerializer, 400: "Invalid data"}
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        logger.info("New user registered", extra={"phone_number": user.phone_number})
        return Response({
            "user": UserSerializer(user).data,
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)


class SendOTPView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [OTPRequestThrottle]

    @extend_schema(
        request=OTPSendSerializer,
        responses={
            200: OpenApiResponse(description="Verification code sent"),
            400: OpenApiResponse(description="Invalid phone number"),
            429: OpenApiResponse(description="Too many requests"),
            500: OpenApiResponse(description="SMS delivery failed"),
        }
    )
    def post(self, request):
        serializer = OTPSendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone_number = serializer.validated_data["phone_number"]

        user, created = User.objects.get_or_create(phone_number=phone_number)
        if created:
            user.set_unusable_password()
            user.save()
            logger.info("New user created during OTP request", extra={"phone_number": phone_number})

        otp_code = OTPCode.generate_code()
        otp = OTPCode.objects.create(user=user, code=otp_code)

        sms_service = KavenegarService()
        success = sms_service.send_verification_code(receptor=phone_number, token=otp.code)
        if not success:
            otp.delete()
            logger.error("Failed to send OTP", extra={"phone_number": phone_number})
            return Response(
                {"detail": "Unable to send verification code. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        logger.info("OTP sent successfully", extra={"phone_number": phone_number})
        return Response({"detail": "Verification code sent successfully."}, status=status.HTTP_200_OK)


class VerifyOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request=OTPVerifySerializer,
        responses={
            200: OpenApiResponse(description="Authentication successful"),
            400: OpenApiResponse(description="Invalid or expired code"),
            404: OpenApiResponse(description="User not found"),
        }
    )
    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone_number = serializer.validated_data["phone_number"]
        code = serializer.validated_data["code"]

        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            logger.warning("OTP verification attempted for non-existent user", extra={"phone_number": phone_number})
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        otp = OTPCode.objects.active().filter(user=user, code=code).first()
        if otp is None:
            latest = OTPCode.objects.filter(user=user).order_by("-created_at").first()
            if latest:
                latest.increase_failed_attempts()
            logger.warning("Invalid OTP attempt", extra={"phone_number": phone_number})
            return Response({"detail": "Invalid or expired verification code."}, status=status.HTTP_400_BAD_REQUEST)

        otp.mark_as_used()
        refresh = RefreshToken.for_user(user)
        logger.info("User authenticated via OTP", extra={"phone_number": phone_number})
        return Response({
            "user": UserSerializer(user).data,
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }, status=status.HTTP_200_OK)