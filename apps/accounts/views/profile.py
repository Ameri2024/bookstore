from rest_framework import generics, permissions
from ..serializers import UserSerializer, UserProfileUpdateSerializer


class UserProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        return UserProfileUpdateSerializer if self.request.method in ['PUT', 'PATCH'] else UserSerializer

    def get_object(self):
        return self.request.user