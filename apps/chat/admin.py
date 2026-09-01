from django.contrib import admin

from .models import Conversation, Message


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'title',
        'created_at',
        'updated_at',
    ]

    list_filter = [
        'created_at',
        'updated_at',
    ]

    search_fields = [
        'user__email',
        'title',
    ]

    readonly_fields = [
        'created_at',
        'updated_at',
    ]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = [
        'conversation',
        'role',
        'short_content',
        'created_at',
    ]

    list_filter = [
        'role',
        'created_at',
    ]

    search_fields = [
        'content',
        'conversation__title',
    ]

    readonly_fields = [
        'created_at',
    ]

    @admin.display(description='Content')
    def short_content(self, obj):
        if len(obj.content) > 50:
            return f'{obj.content[:50]}...'

        return obj.content