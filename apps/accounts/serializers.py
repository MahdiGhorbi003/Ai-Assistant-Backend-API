from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password

from .models import CustomUser


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = (
            'id',
            'email',
            'first_name',
            'last_name',
            'date_joined',
        )

        read_only_fields = (
            'date_joined',
        )


class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = (
            'email',
            'password',
        )

    def create(self, validated_data):
        return CustomUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
        )

    def validate_password(self, password):
        validate_password(password)
        return password

    def validate_email(self, email):
        if CustomUser.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                'This email is already registered.'
            )
        return email