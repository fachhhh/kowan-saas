from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Tenant, User, Product


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (('Tenant', {'fields': ('tenant',)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (('Tenant', {'fields': ('tenant',)}),)
    list_display = UserAdmin.list_display + ('tenant',)


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ('nama', 'dibuat_pada')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('nama', 'tenant', 'harga', 'stok')
    list_filter = ('tenant',)