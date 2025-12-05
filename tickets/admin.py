from django.contrib import admin

from .models import Message, Ticket


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "subject",
        "author",
        "status",
        "priority",
        "category",
        "department",
        "is_auto_solved",
        "created_at",
    )
    list_filter = ("status", "priority", "category", "department", "is_auto_solved")
    search_fields = ("subject", "description", "author__username", "author__full_name")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "ticket", "is_bot", "created_at")
    list_filter = ("is_bot", "created_at")
    search_fields = ("text",)
