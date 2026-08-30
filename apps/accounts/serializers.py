from rest_framework import serializers

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
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = (
            'email',
            'password',
        )

    def create(self, validated_data):
        return CustomUser.objects.create_user(
            validated_data['email'],
            validated_data['password'],
        )
