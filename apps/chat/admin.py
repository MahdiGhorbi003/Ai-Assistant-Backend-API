from django.contrib import admin

from .models import Conversation


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