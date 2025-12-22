from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

# Enhanced User Admin with modern styling
class CustomUserAdmin(UserAdmin):
    """
    Enhanced User admin with modern Jazzmin styling
    """
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('-date_joined',)
    list_per_page = 25
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser'),
            'classes': ('collapse',),
        }),
    )

# Custom admin configuration
class BaseModelAdmin(admin.ModelAdmin):
    """
    Base admin class with common Jazzmin-compatible configuration
    """
    list_per_page = 25
    save_on_top = True
    show_full_result_count = False  # Performance optimization

# Re-register User with custom admin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# Customize admin site headers
admin.site.site_header = "Gaming Analytics Administration"
admin.site.site_title = "Gaming Analytics Admin"
admin.site.index_title = "Welcome to Gaming Analytics Admin Portal"
