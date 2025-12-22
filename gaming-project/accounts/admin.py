from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

class GamingAnalyticsAdminSite(AdminSite):
    """
    Custom admin site for Gaming Analytics with modern theming
    """
    site_title = _('Gaming Analytics Admin')
    site_header = _('Gaming Analytics Administration')
    index_title = _('Gaming Analytics Dashboard')
    site_brand = _('Gaming Analytics')
    
    def each_context(self, request):
        """
        Add custom context to all admin pages
        """
        context = super().each_context(request)
        context.update({
            'site_brand': self.site_brand,
            'has_permission': request.user.is_active and request.user.is_staff,
        })
        return context

# Create custom admin site instance
admin_site = GamingAnalyticsAdminSite(name='gaming_admin')

# Custom admin configuration
class BaseModelAdmin(admin.ModelAdmin):
    """
    Base admin class with common configuration
    """
    list_per_page = 25
    save_on_top = True
    
    class Media:
        css = {
            'all': ('admin/css/admin_custom.css',)
        }
        js = (
            'admin/js/admin_enhancements.js',
        )

# Enhanced User Admin
class CustomUserAdmin(UserAdmin):
    """
    Enhanced User admin with modern styling
    """
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('-date_joined',)
    
    class Media:
        css = {
            'all': ('admin/css/admin_custom.css',)
        }

# Re-register User with custom admin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

def get_admin_colors():
    """
    Return the color scheme for admin interface
    """
    return {
        'primary': '#8B0000',
        'primary_dark': '#660000',
        'primary_light': '#A31414',
        'secondary': '#DC143C',
        'accent': '#B22222',
        'success': '#10B981',
        'danger': '#EF4444',
        'warning': '#F59E0B',
        'info': '#3B82F6',
    }
