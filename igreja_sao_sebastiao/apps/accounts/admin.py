from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from unfold.admin import ModelAdmin


class UserAdmin(BaseUserAdmin, ModelAdmin):
    list_display = ("username", "email", "get_full_name", "is_active", "is_staff", "date_joined")
    list_filter = ("is_active", "is_staff", "is_superuser", "groups")
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("-date_joined",)

    fieldsets = BaseUserAdmin.fieldsets + (("Segurança", {"fields": ("failed_login_attempts", "last_failed_login")}),)


class AuditLogAdmin(ModelAdmin):
    list_display = ("user", "action", "entity_type", "entity_id", "ip_address", "created_at")
    list_filter = ("action", "entity_type", "created_at")
    search_fields = ("action", "entity_type", "entity_id", "user__username")
    readonly_fields = (
        "user",
        "action",
        "entity_type",
        "entity_id",
        "old_value",
        "new_value",
        "ip_address",
        "created_at",
    )
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
