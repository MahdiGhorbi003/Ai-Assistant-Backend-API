from rest_framework import serializers

from .models import Conversation, Message


class ConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = [
            'id',
            'title',
            'created_at',
            'updated_at',
        ]

        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
        ]

    def validate_title(self, value):
        return value.strip()


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = [
            'id',
            'conversation',
            'role',
            'content',
            'created_at',
        ]

        read_only_fields = [
            'id',
            'role',
            'created_at',
        ]

    def validate_content(self, value):
        return value.strip()