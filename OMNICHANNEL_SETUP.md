# 🌐 Настройка омниканальной системы приёма обращений

## Обзор

Система Centrium поддерживает приём обращений из множества каналов:
- **Веб-портал** - встроенный чат на сайте
- **Email** - автоматическая обработка писем
- **Telegram** - бот для мессенджера
- **WhatsApp** - интеграция через API
- **External API** - для интеграции со сторонними системами

Все обращения обрабатываются единым AI-ассистентом и автоматически создают тикеты в системе.

---

## 📧 Настройка Email интеграции

### 1. Настройте переменные окружения в `.env`:

```env
SUPPORT_EMAIL=support@kazaktelecom.kz
SUPPORT_EMAIL_PASSWORD=your-app-password
EMAIL_IMAP_SERVER=imap.gmail.com
EMAIL_IMAP_PORT=993
```

### 2. Для Gmail создайте App Password:
1. Перейдите в настройки Google Account
2. Security → 2-Step Verification
3. App passwords → Generate new password
4. Используйте сгенерированный пароль в `SUPPORT_EMAIL_PASSWORD`

### 3. Запустите проверку email вручную:

```bash
python manage.py check_emails
```

### 4. Настройте автоматическую проверку (cron/планировщик):

**Linux/Mac (crontab):**
```bash
*/5 * * * * cd /path/to/project && python manage.py check_emails
```

**Windows (Task Scheduler):**
- Создайте задачу, которая запускает `check_emails.bat` каждые 5 минут

---

## 🤖 Настройка Telegram Bot

### 1. Создайте бота через @BotFather:

1. Откройте Telegram и найдите @BotFather
2. Отправьте `/newbot`
3. Следуйте инструкциям и получите токен

### 2. Добавьте токен в `.env`:

```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```

### 3. Установите webhook:

```python
from tickets.integrations.telegram_integration import TelegramIntegration

telegram = TelegramIntegration()
telegram.set_webhook("https://your-domain.com/tickets/api/telegram/webhook/")
```

Или через curl:
```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://your-domain.com/tickets/api/telegram/webhook/"}'
```

### 4. Для локальной разработки используйте ngrok:

```bash
ngrok http 8000
# Используйте полученный https URL для webhook
```

---

## 🔌 Использование External API

### 1. Настройте API ключ в `.env`:

```env
EXTERNAL_API_KEY=your-secure-random-api-key-here
```

### 2. Отправляйте запросы на endpoint:

**URL:** `POST /tickets/api/external/message/`

**Request Body (JSON):**
```json
{
  "api_key": "your-secure-random-api-key-here",
  "user_identifier": "user@example.com",
  "text": "У меня не работает интернет",
  "image_base64": "base64_encoded_image_data",  // опционально
  "external_id": "crm-ticket-12345",  // опционально
  "metadata": {  // опционально
    "full_name": "Иванов Иван Иванович",
    "email": "user@example.com",
    "phone": "+77001234567"
  }
}
```

**Response:**
```json
{
  "success": true,
  "ticket_id": 123,
  "reply": "Здравствуйте! Я помогу решить проблему с интернетом...",
  "needs_escalation": false,
  "status": "new"
}
```

### 3. Пример использования (Python):

```python
import requests
import base64

# Подготовка данных
with open("screenshot.jpg", "rb") as f:
    image_base64 = base64.b64encode(f.read()).decode()

# Отправка запроса
response = requests.post(
    "https://your-domain.com/tickets/api/external/message/",
    json={
        "api_key": "your-api-key",
        "user_identifier": "client@example.com",
        "text": "Проблема с роутером",
        "image_base64": image_base64,
        "metadata": {
            "full_name": "Петров Петр",
            "phone": "+77001234567"
        }
    }
)

result = response.json()
print(f"Ticket ID: {result['ticket_id']}")
print(f"AI Reply: {result['reply']}")
```

---

## 🗄️ Миграция базы данных

После настройки интеграций выполните миграции:

```bash
python manage.py makemigrations
python manage.py migrate
```

Это создаст:
- Модель `Channel` для управления каналами
- Поля `channel` и `external_id` в модели `Ticket`

---

## 📊 Мониторинг каналов

### Проверка статуса API:

```bash
curl https://your-domain.com/tickets/api/status/
```

**Response:**
```json
{
  "status": "ok",
  "version": "1.0",
  "channels": {
    "web": true,
    "email": true,
    "telegram": true,
    "api": true
  }
}
```

### Просмотр тикетов по каналам:

В панели оператора все тикеты отображаются с иконкой канала:
- 🌐 Веб-портал
- ✉️ Email
- 📱 Telegram
- 💬 WhatsApp
- 🔌 API

---

## 🔐 Безопасность

1. **API ключи:** Используйте длинные случайные строки (минимум 32 символа)
2. **HTTPS:** Обязательно используйте HTTPS для production
3. **Rate limiting:** Настройте ограничение запросов для API endpoints
4. **Webhook validation:** Telegram webhook автоматически валидируется

---

## 🧪 Тестирование

### Тест Email интеграции:
```bash
python manage.py check_emails
```

### Тест External API:
```bash
curl -X POST http://localhost:8000/tickets/api/external/message/ \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "your-api-key",
    "user_identifier": "test@example.com",
    "text": "Тестовое обращение"
  }'
```

### Тест Telegram:
Отправьте сообщение вашему боту в Telegram

---

## 📝 Логирование

Все интеграции логируют свою работу. Проверяйте логи:

```bash
# Django logs
tail -f logs/django.log

# Или в консоли при DEBUG=True
python manage.py runserver
```

---

## 🆘 Troubleshooting

### Email не приходят:
- Проверьте IMAP настройки
- Убедитесь, что App Password корректный
- Проверьте firewall/антивирус

### Telegram webhook не работает:
- Убедитесь, что URL доступен из интернета (используйте ngrok для теста)
- Проверьте, что webhook установлен: `curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo`

### API возвращает 401:
- Проверьте API ключ в запросе и `.env`
- Убедитесь, что ключи совпадают

---

## 📚 Дополнительные ресурсы

- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Gmail IMAP Settings](https://support.google.com/mail/answer/7126229)
- [Django Management Commands](https://docs.djangoproject.com/en/5.0/howto/custom-management-commands/)
