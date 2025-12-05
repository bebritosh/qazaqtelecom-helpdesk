from django.conf import settings
from django.db import models


class Channel(models.Model):
    """Модель для отслеживания каналов коммуникации"""
    CHANNEL_WEB = "web"
    CHANNEL_EMAIL = "email"
    CHANNEL_TELEGRAM = "telegram"
    CHANNEL_WHATSAPP = "whatsapp"
    CHANNEL_API = "api"
    
    CHANNEL_CHOICES = [
        (CHANNEL_WEB, "Веб-портал"),
        (CHANNEL_EMAIL, "Email"),
        (CHANNEL_TELEGRAM, "Telegram"),
        (CHANNEL_WHATSAPP, "WhatsApp"),
        (CHANNEL_API, "API"),
    ]
    
    name = models.CharField(max_length=20, choices=CHANNEL_CHOICES, unique=True)
    is_active = models.BooleanField(default=True)
    config = models.JSONField(default=dict, blank=True, help_text="Конфигурация канала (токены, webhook URL и т.д.)")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self) -> str:
        return self.get_name_display()
    
    class Meta:
        verbose_name = "Канал коммуникации"
        verbose_name_plural = "Каналы коммуникации"


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
    channel = models.CharField(
        max_length=20,
        choices=Channel.CHANNEL_CHOICES,
        default=Channel.CHANNEL_WEB,
        help_text="Канал, через который поступило обращение"
    )
    external_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="ID обращения во внешней системе (email message-id, telegram chat_id и т.д.)"
    )
    assigned_operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="assigned_tickets",
        null=True,
        blank=True,
        help_text="Оператор, назначенный на тикет"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_NEW)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default=PRIORITY_MEDIUM)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default=CATEGORY_OTHER)
    department = models.CharField(max_length=20, choices=DEPARTMENT_CHOICES, default=DEPT_TECHNICAL)
    subject = models.CharField(max_length=255)
    description = models.TextField()
    is_auto_solved = models.BooleanField(default=False)
    escalated_at = models.DateTimeField(null=True, blank=True, help_text="Время эскалации к оператору")
    operator_joined = models.BooleanField(default=False, help_text="Оператор присоединился к чату")
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
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Отправитель сообщения (пользователь или оператор)"
    )
    text = models.TextField(blank=True)
    image = models.ImageField(upload_to="ticket_images/", blank=True, null=True)
    is_bot = models.BooleanField(default=False)
    rating = models.IntegerField(
        null=True,
        blank=True,
        choices=[(1, "Helpful"), (-1, "Not Helpful")],
        help_text="Оценка ответа AI: 1 = полезно, -1 = не полезно"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Message {self.id} for ticket {self.ticket_id}"


class KnowledgeArticle(models.Model):
    """База знаний - статьи с решениями проблем"""
    STATUS_DRAFT = "draft"
    STATUS_PUBLISHED = "published"
    STATUS_ARCHIVED = "archived"
    
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Черновик"),
        (STATUS_PUBLISHED, "Опубликовано"),
        (STATUS_ARCHIVED, "Архив"),
    ]
    
    title = models.CharField(max_length=255, verbose_name="Заголовок")
    slug = models.SlugField(max_length=255, unique=True, verbose_name="URL")
    content = models.TextField(verbose_name="Содержание (Markdown)")
    summary = models.TextField(max_length=500, verbose_name="Краткое описание")
    
    category = models.CharField(
        max_length=20,
        choices=Ticket.CATEGORY_CHOICES,
        default=Ticket.CATEGORY_OTHER,
        verbose_name="Категория"
    )
    
    tags = models.CharField(
        max_length=255,
        blank=True,
        help_text="Теги через запятую: роутер, интернет, настройка"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT,
        verbose_name="Статус"
    )
    
    # Связь с тикетом, из которого создана статья
    source_ticket = models.ForeignKey(
        Ticket,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="knowledge_articles",
        help_text="Тикет, из которого создана статья"
    )
    
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="knowledge_articles",
        verbose_name="Автор"
    )
    
    views_count = models.IntegerField(default=0, verbose_name="Просмотры")
    helpful_count = models.IntegerField(default=0, verbose_name="Полезно")
    not_helpful_count = models.IntegerField(default=0, verbose_name="Не полезно")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Статья базы знаний"
        verbose_name_plural = "База знаний"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "-published_at"]),
            models.Index(fields=["category"]),
        ]
    
    def __str__(self) -> str:
        return self.title
    
    def get_tags_list(self):
        """Возвращает список тегов"""
        return [tag.strip() for tag in self.tags.split(",") if tag.strip()]
    
    def increment_views(self):
        """Увеличивает счётчик просмотров"""
        self.views_count += 1
        self.save(update_fields=["views_count"])
    
    def mark_helpful(self, is_helpful: bool):
        """Отмечает статью как полезную или нет"""
        if is_helpful:
            self.helpful_count += 1
        else:
            self.not_helpful_count += 1
        self.save(update_fields=["helpful_count", "not_helpful_count"])
    
    @property
    def helpfulness_score(self):
        """Процент полезности"""
        total = self.helpful_count + self.not_helpful_count
        if total == 0:
            return 0
        return int((self.helpful_count / total) * 100)


class Notification(models.Model):
    """Уведомления для операторов о новых эскалациях"""
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Notification for {self.operator.username}: {self.message}"
