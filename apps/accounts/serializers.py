from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

PHONE_NUMBER_FIELD = serializers.RegexField(
    regex=r"^09\d{9}$",
    max_length=11,
    error_messages={"invalid": "Enter a valid Iranian mobile phone number."},
)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "phone_number", "first_name", "last_name", "email", "address", "postal_code"]
        read_only_fields = ["id", "phone_number"]


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "address", "postal_code"]


class UserRegisterSerializer(serializers.ModelSerializer):
    phone_number = PHONE_NUMBER_FIELD

    class Meta:
        model = User
        fields = ["phone_number"]

    def create(self, validated_data):
        user = User.objects.create_user(phone_number=validated_data["phone_number"])
        user.set_unusable_password()
        user.save()
        return user


class OTPSendSerializer(serializers.Serializer):
    phone_number = PHONE_NUMBER_FIELD


class OTPVerifySerializer(serializers.Serializer):
    phone_number = PHONE_NUMBER_FIELD
    code = serializers.RegexField(
        regex=r"^\d{6}$",
        error_messages={"invalid": "OTP code must contain exactly six digits."},
    )