from rest_framework import generics, permissions
from drf_spectacular.utils import extend_schema

from .serializers import RegisterSerializer


@extend_schema(
    tags=['Authentication'],
    auth=[],
    summary='Register a new user',
    description='Create a new user account using email and password.',
)
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
