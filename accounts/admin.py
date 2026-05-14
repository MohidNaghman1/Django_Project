from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import PasswordResetToken, User, VirtualWallet


class VirtualWalletInline(admin.TabularInline):
	model = VirtualWallet
	fields = ("balance", "currency", "created_at")
	readonly_fields = ("created_at",)
	extra = 0


@admin.register(User)
class UserAdmin(BaseUserAdmin):
	inlines = (VirtualWalletInline,)
	ordering = ("email",)
	list_display = ("email", "full_name", "age", "father_name", "is_active", "is_staff")
	search_fields = ("email", "full_name")
	readonly_fields = ("created_at", "last_login")
	fieldsets = (
		(None, {"fields": ("email", "password")}),
		("Personal info", {"fields": ("full_name", "age", "father_name", "profile_image")}),
		("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
		("Important dates", {"fields": ("last_login", "created_at")}),
	)
	add_fieldsets = (
		(None, {
			"classes": ("wide",),
			"fields": ("email", "full_name", "age", "father_name", "profile_image", "password1", "password2", "is_staff", "is_active"),
		}),
	)


@admin.register(VirtualWallet)
class VirtualWalletAdmin(admin.ModelAdmin):
	list_display = ("user", "balance", "currency", "created_at")
	search_fields = ("user__email", "user__full_name")
	list_select_related = ("user",)


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
	list_display = ("user", "token", "is_used", "created_at")
	search_fields = ("user__email", "token")
	list_filter = ("is_used", "created_at")
	list_select_related = ("user",)
