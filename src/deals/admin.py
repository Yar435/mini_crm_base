from django.contrib import admin

from .models import Deal, Manager


@admin.register(Manager)
class ManagerAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "email", "phone")
    search_fields = ("name", "email")


@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "amount",
        "status",
        "client",
        "manager",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = ("title",)
    autocomplete_fields = ("client", "manager")
