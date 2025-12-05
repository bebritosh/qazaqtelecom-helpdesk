# 📚 База знаний Centrium - Руководство

## 🎯 Обзор

Умная база знаний с автоматической генерацией статей из решённых тикетов, поиском и рекомендациями.

### Ключевые возможности:
- ✅ Автоматическое создание статей из тикетов через AI
- ✅ Markdown редактор с live preview
- ✅ Полнотекстовый поиск по статьям
- ✅ Рекомендации похожих решений
- ✅ Рейтинг полезности статей
- ✅ Категоризация и теги
- ✅ Счётчик просмотров
- ✅ Статусы: черновик/опубликовано/архив

---

## 🚀 Быстрый старт

### 1. Создание статьи из тикета (автоматически)

```python
from tickets.knowledge_service import KnowledgeBaseService
from tickets.models import Ticket

# Получаем решённый тикет
ticket = Ticket.objects.get(id=123, status=Ticket.STATUS_CLOSED)

# Генерируем статью
article = KnowledgeBaseService.generate_article_from_ticket(
    ticket=ticket,
    author=request.user
)

print(f"Создана статья: {article.title}")
print(f"URL для редактирования: /knowledge/edit/{article.id}/")
```

### 2. Создание статьи вручную

1. Открой `/knowledge/edit/new/`
2. Заполни форму:
   - **Заголовок**: Как настроить роутер
   - **Описание**: Пошаговая инструкция
   - **Содержание**: Markdown текст
   - **Категория**: Internet
   - **Теги**: роутер, настройка, wifi
   - **Статус**: Черновик
3. Нажми "Сохранить"
4. Проверь в preview
5. Измени статус на "Опубликовано"

### 3. Поиск статей

```python
from tickets.knowledge_service import KnowledgeBaseService

# Поиск по запросу
articles = KnowledgeBaseService.search_articles(
    query="роутер не работает",
    category="internet",
    limit=10
)

# Популярные статьи
popular = KnowledgeBaseService.get_popular_articles(limit=5)

# Самые полезные
helpful = KnowledgeBaseService.get_helpful_articles(limit=5)
```

---

## 📝 Markdown синтаксис

### Заголовки
```markdown
# Заголовок 1
## Заголовок 2
### Заголовок 3
```

### Форматирование текста
```markdown
**Жирный текст**
*Курсивный текст*
`Код`
```

### Списки
```markdown
* Элемент 1
* Элемент 2
* Элемент 3

1. Первый шаг
2. Второй шаг
3. Третий шаг
```

### Код блоки
```markdown
```python
def hello():
    print("Hello, World!")
```
```

### Цитаты
```markdown
> Это важная цитата
```

### Ссылки
```markdown
[Текст ссылки](https://example.com)
```

---

## 🎨 Структура статьи (рекомендации)

```markdown
# Как решить проблему с интернетом

## Проблема
Описание проблемы, с которой столкнулся пользователь.

## Симптомы
- Не горит индикатор на роутере
- Нет подключения к Wi-Fi
- Медленная скорость

## Решение

### Шаг 1: Проверка подключения
1. Проверьте кабель питания
2. Убедитесь, что роутер включён
3. Проверьте индикаторы

### Шаг 2: Перезагрузка роутера
1. Отключите питание на 30 секунд
2. Включите обратно
3. Подождите 2-3 минуты

### Шаг 3: Проверка настроек
```
IP: 192.168.1.1
Логин: admin
Пароль: admin
```

## Дополнительно
- Если не помогло, обратитесь к оператору
- Проверьте баланс счёта
- Убедитесь, что нет технических работ

## Полезные ссылки
- [Официальный сайт](https://kazaktelecom.kz)
- [Инструкция к роутеру](https://example.com)
```

---

## 🔧 API Endpoints

### Публичные

#### GET `/knowledge/`
Список всех опубликованных статей

**Параметры:**
- `q` - поисковый запрос
- `category` - фильтр по категории

**Пример:**
```
/knowledge/?q=роутер&category=internet
```

#### GET `/knowledge/<slug>/`
Просмотр статьи

**Пример:**
```
/knowledge/kak-nastroit-router-123/
```

#### POST `/knowledge/api/rate/<article_id>/`
Оценка статьи

**Body:**
```json
{
  "is_helpful": true
}
```

**Response:**
```json
{
  "success": true,
  "helpful_count": 42,
  "not_helpful_count": 3,
  "score": 93
}
```

### Для операторов

#### GET `/knowledge/api/search/`
Поиск для автокомплита

**Параметры:**
- `q` - запрос (минимум 2 символа)
- `category` - категория

**Response:**
```json
{
  "results": [
    {
      "id": 1,
      "title": "Как настроить роутер",
      "summary": "Пошаговая инструкция...",
      "url": "/knowledge/kak-nastroit-router-123/",
      "category": "Internet",
      "views": 150,
      "helpfulness": 95
    }
  ]
}
```

#### POST `/knowledge/create-from-ticket/<ticket_id>/`
Создать статью из тикета

**Response:**
```json
{
  "success": true,
  "article_id": 5,
  "redirect_url": "/knowledge/edit/5/"
}
```

#### GET `/knowledge/api/suggest/<ticket_id>/`
Предложить статьи для тикета

**Response:**
```json
{
  "suggestions": [
    {
      "id": 1,
      "title": "Похожая проблема",
      "summary": "...",
      "url": "/knowledge/...",
      "helpfulness": 90
    }
  ]
}
```

---

## 🎯 Интеграция с чатом

### Автоматические рекомендации

При создании тикета AI автоматически ищет похожие статьи:

```python
# В chat.js
function suggestKnowledgeArticles(ticketId) {
  fetch(`/knowledge/api/suggest/${ticketId}/`)
    .then(res => res.json())
    .then(data => {
      if (data.suggestions.length > 0) {
        showSuggestions(data.suggestions);
      }
    });
}

function showSuggestions(articles) {
  const html = `
    <div class="knowledge-suggestions">
      <h4>💡 Возможно, эти статьи помогут:</h4>
      ${articles.map(a => `
        <a href="${a.url}" target="_blank">
          ${a.title} (${a.helpfulness}% полезно)
        </a>
      `).join('')}
    </div>
  `;
  // Показываем в чате
}
```

---

## 📊 Аналитика

### Популярные статьи
```python
from tickets.models import KnowledgeArticle

top_viewed = KnowledgeArticle.objects.filter(
    status=KnowledgeArticle.STATUS_PUBLISHED
).order_by('-views_count')[:10]

for article in top_viewed:
    print(f"{article.title}: {article.views_count} просмотров")
```

### Самые полезные
```python
top_helpful = KnowledgeArticle.objects.filter(
    status=KnowledgeArticle.STATUS_PUBLISHED,
    helpful_count__gt=0
).order_by('-helpful_count')[:10]

for article in top_helpful:
    score = article.helpfulness_score
    print(f"{article.title}: {score}% полезно")
```

### Статистика по категориям
```python
from django.db.models import Count, Avg

stats = KnowledgeArticle.objects.filter(
    status=KnowledgeArticle.STATUS_PUBLISHED
).values('category').annotate(
    count=Count('id'),
    avg_views=Avg('views_count'),
    avg_helpful=Avg('helpful_count')
)

for stat in stats:
    print(f"{stat['category']}: {stat['count']} статей, {stat['avg_views']} просмотров")
```

---

## 🤖 Автоматизация

### Автоматическое создание статей

Добавь в `tickets/views.py` после закрытия тикета:

```python
# После успешного решения проблемы
if ticket.status == Ticket.STATUS_CLOSED and ticket.is_auto_solved:
    # Автоматически создаём статью
    from tickets.knowledge_service import KnowledgeBaseService
    
    article = KnowledgeBaseService.generate_article_from_ticket(
        ticket=ticket,
        author=request.user
    )
    
    if article:
        # Уведомляем оператора для проверки
        Notification.objects.create(
            operator=request.user,
            ticket=ticket,
            message=f"Создана статья базы знаний: {article.title}"
        )
```

### Еженедельный дайджест

```python
# management/commands/weekly_knowledge_digest.py
from django.core.management.base import BaseCommand
from tickets.models import KnowledgeArticle
from datetime import timedelta
from django.utils import timezone

class Command(BaseCommand):
    def handle(self, *args, **options):
        week_ago = timezone.now() - timedelta(days=7)
        
        new_articles = KnowledgeArticle.objects.filter(
            status=KnowledgeArticle.STATUS_PUBLISHED,
            published_at__gte=week_ago
        )
        
        print(f"Новых статей за неделю: {new_articles.count()}")
        for article in new_articles:
            print(f"- {article.title} ({article.views_count} просмотров)")
```

---

## 🎨 Кастомизация

### Изменить шаблон статьи

Редактируй `templates/knowledge/detail.html`:

```html
<!-- Добавить кнопку "Поделиться" -->
<div class="share-buttons">
  <a href="https://t.me/share/url?url={{ request.build_absolute_uri }}">
    <i class="bi bi-telegram"></i> Поделиться
  </a>
</div>
```

### Добавить новые категории

В `tickets/models.py`:

```python
CATEGORY_CHOICES = [
    (CATEGORY_INTERNET, "Internet"),
    (CATEGORY_TV, "TV"),
    (CATEGORY_BILLING, "Billing"),
    (CATEGORY_MOBILE, "Mobile"),  # Новая категория
    (CATEGORY_OTHER, "Other"),
]
```

### Изменить Markdown парсер

Для более продвинутого парсинга установи:

```bash
pip install markdown
```

В `templates/knowledge/detail.html`:

```python
{% load markdown_extras %}

<div class="markdown-content">
  {{ article.content|markdown }}
</div>
```

---

## 🐛 Troubleshooting

### Статья не создаётся из тикета

**Проблема:** `generate_article_from_ticket()` возвращает `None`

**Решение:**
1. Проверь, что тикет закрыт: `ticket.status == Ticket.STATUS_CLOSED`
2. Проверь, что есть сообщения: `ticket.messages.count() >= 2`
3. Проверь API ключ Gemini в `.env`

### Markdown не отображается

**Проблема:** Видны сырые Markdown теги

**Решение:**
1. Проверь, что JavaScript загружен
2. Открой консоль браузера (F12)
3. Убедись, что `parseMarkdown()` вызывается

### Поиск не находит статьи

**Проблема:** Поиск возвращает пустой результат

**Решение:**
1. Проверь статус статей: должны быть `PUBLISHED`
2. Проверь регистр: поиск case-insensitive
3. Попробуй более короткий запрос

---

## 📚 Примеры использования

### Пример 1: Создание статьи вручную

```python
from tickets.models import KnowledgeArticle, Ticket
from django.utils.text import slugify

article = KnowledgeArticle.objects.create(
    title="Как перезагрузить роутер",
    slug=slugify("Как перезагрузить роутер"),
    content="""
# Как перезагрузить роутер

## Способ 1: Кнопка на роутере
1. Найдите кнопку Reset
2. Нажмите и удерживайте 3 секунды

## Способ 2: Через веб-интерфейс
1. Откройте 192.168.1.1
2. Войдите (admin/admin)
3. Нажмите "Перезагрузка"
    """,
    summary="Два способа перезагрузки роутера",
    category=Ticket.CATEGORY_INTERNET,
    tags="роутер, перезагрузка, reset",
    status=KnowledgeArticle.STATUS_PUBLISHED,
    author=request.user
)
```

### Пример 2: Поиск и рекомендации

```python
# В чате, когда пользователь пишет
user_query = "роутер не работает"

# Ищем статьи
suggestions = KnowledgeBaseService.suggest_articles_for_user_query(
    query=user_query,
    limit=3
)

# Показываем пользователю
if suggestions:
    message = "💡 Возможно, эти статьи помогут:\n"
    for article in suggestions:
        message += f"- {article['title']}: {article['url']}\n"
    
    # Отправляем в чат
    appendMessage(message, isBot=True)
```

---

## ✅ Checklist для операторов

При создании статьи проверь:

- [ ] Заголовок понятный и описывает проблему
- [ ] Краткое описание заполнено
- [ ] Содержание структурировано (заголовки, списки)
- [ ] Есть пошаговая инструкция
- [ ] Добавлены теги
- [ ] Выбрана правильная категория
- [ ] Проверен preview
- [ ] Статус "Опубликовано"
- [ ] Нет опечаток и ошибок

---

База знаний готова! 🎉

Теперь каждый решённый тикет может стать полезной статьей для других пользователей.
