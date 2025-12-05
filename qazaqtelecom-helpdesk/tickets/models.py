from django.conf import settings
from django.db import models


class Ticket(models.Model):
    STATUS_NEW = "new"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_CLOSED = "closed"

    STATUS_CHOICES = [
        (STATUS_NEW, "New"),
        (STATUS_IN_PROGRESS, "In progress"),
        (STATUS_CLOSED, "Closed"),
    ]

    PRIORITY_LOW = "low"
    PRIORITY_MEDIUM = "medium"
    PRIORITY_HIGH = "high"

    PRIORITY_CHOICES = [
        (PRIORITY_LOW, "Low"),
        (PRIORITY_MEDIUM, "Medium"),
        (PRIORITY_HIGH, "High"),
    ]

    CATEGORY_INTERNET = "internet"
    CATEGORY_TV = "tv"
    CATEGORY_BILLING = "billing"
    CATEGORY_OTHER = "other"

    CATEGORY_CHOICES = [
        (CATEGORY_INTERNET, "Internet"),
        (CATEGORY_TV, "TV"),
        (CATEGORY_BILLING, "Billing"),
        (CATEGORY_OTHER, "Other"),
    ]

    DEPT_TECHNICAL = "technical"
    DEPT_FINANCIAL = "financial"
    DEPT_SALES = "sales"

    DEPARTMENT_CHOICES = [
        (DEPT_TECHNICAL, "Technical"),
        (DEPT_FINANCIAL, "Financial"),
        (DEPT_SALES, "Sales"),
    ]

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tickets",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_NEW)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default=PRIORITY_MEDIUM)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default=CATEGORY_OTHER)
    department = models.CharField(max_length=20, choices=DEPARTMENT_CHOICES, default=DEPT_TECHNICAL)
    subject = models.CharField(max_length=255)
    description = models.TextField()
    is_auto_solved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"#{self.id} {self.subject}"


class Message(models.Model):
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    text = models.TextField(blank=True)
    image = models.ImageField(upload_to="ticket_images/", blank=True, null=True)
    is_bot = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Message {self.id} for ticket {self.ticket_id}"
