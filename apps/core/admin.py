from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, AuditLog


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Informations CNETP', {'fields': ('phone', 'province', 'bio', 'profile_picture')}),
        ('Permissions CNETP', {'fields': ('is_expert', 'is_ctc_staff', 'is_minister')}),
    )
    list_display = ('username', 'get_full_name', 'email', 'is_expert', 'is_ctc_staff', 'is_minister', 'created_at')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('is_expert', 'is_ctc_staff', 'is_minister', 'created_at')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'action', 'content_type', 'user', 'ip_address')
    list_filter = ('action', 'content_type', 'timestamp')
    search_fields = ('user__username', 'object_repr', 'ip_address')
    readonly_fields = ('timestamp', 'user', 'changes', 'ip_address', 'user_agent')
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
