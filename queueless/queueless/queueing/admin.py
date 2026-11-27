from django.contrib import admin

from .models import Office, QueueTicket, Service


@admin.register(Office)
class OfficeAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "location", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "code")


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "office", "is_available")
    list_filter = ("office", "is_available")
    search_fields = ("name",)


@admin.register(QueueTicket)
class QueueTicketAdmin(admin.ModelAdmin):
    list_display = ("code", "student", "office", "service", "status", "queue_date")
    list_filter = ("status", "office", "queue_date")
    search_fields = ("student__username",)