from django.contrib.auth.admin import UserAdmin
from django.contrib import admin

from .models import CustomUser
from .forms import CustomUserCreationForm, CustomUserChangeForm


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm

    list_display = [
        'email',
        'is_staff',
        'is_active',
        'is_superuser',
        'date_joined',
    ]

    search_fields = [
        'email',
    ]

    list_filter = [
        'is_staff',
        'is_active',
        'is_superuser',
    ]

    ordering = [
        'email',
    ]

    readonly_fields = [
        'date_joined',
        'last_login',
    ]

    fieldsets = (
        (
            'Authentication',
            {
                'fields': (
                    'email',
                    'password',
                )
            },
        ),
        (
            'Personal information',
            {
                'fields': (
                    'first_name',
                    'last_name',
                    'birth_date',
                )
            },
        ),
        (
            'Permissions',
            {
                'fields': (
                    'is_active',
                    'is_staff',
                    'is_superuser',
                    'groups',
                    'user_permissions',
                )
            },
        ),
        (
            'Important dates',
            {
                'fields': (
                    'date_joined',
                    'last_login',
                )
            },
        ),

    )

    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': (
                    'email',
                    'password1',
                    'password2',
                ),
            },
        ),
    )
