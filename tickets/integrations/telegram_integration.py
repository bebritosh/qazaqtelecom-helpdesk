"""
Интеграция с Telegram Bot для приёма обращений
"""
import requests
import logging
from typing import Dict, Any, Optional
from django.conf import settings
from django.http import JsonResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from ..channel_handler import ChannelHandler
from ..models import Channel

logger = logging.getLogger(__name__)


class TelegramIntegration:
    """Обработчик Telegram Bot webhook"""
    
    def __init__(self):
        self.bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    def send_message(self, chat_id: int, text: str) -> bool:
        """Отправляет сообщение в Telegram"""
        if not self.bot_token:
            logger.warning("Telegram bot token not configured")
            return False
        
        try:
            response = requests.post(
                f"{self.api_url}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "HTML"
                },
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False
    
    def download_photo(self, file_id: str) -> Optional[bytes]:
        """Скачивает фото из Telegram"""
        if not self.bot_token:
            return None
        
        try:
            # Получаем информацию о файле
            response = requests.get(
                f"{self.api_url}/getFile",
                params={"file_id": file_id},
                timeout=10
            )
            
            if response.status_code != 200:
                return None
            
            file_path = response.json()['result']['file_path']
            
            # Скачиваем файл
            file_url = f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}"
            file_response = requests.get(file_url, timeout=10)
            
            if file_response.status_code == 200:
                return file_response.content
            
        except Exception as e:
            logger.error(f"Failed to download Telegram photo: {e}")
        
        return None
    
    def set_webhook(self, webhook_url: str) -> bool:
        """Устанавливает webhook URL для бота"""
        if not self.bot_token:
            logger.warning("Telegram bot token not configured")
            return False
        
        try:
            response = requests.post(
                f"{self.api_url}/setWebhook",
                json={"url": webhook_url},
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to set Telegram webhook: {e}")
            return False


@csrf_exempt
def telegram_webhook(request: HttpRequest) -> JsonResponse:
    """
    Webhook endpoint для Telegram Bot
    URL: /tickets/api/telegram/webhook/
    """
    if request.method != 'POST':
        return JsonResponse({"error": "Method not allowed"}, status=405)
    
    try:
        import json
        data = json.loads(request.body)
        
        # Проверяем наличие сообщения
        if 'message' not in data:
            return JsonResponse({"ok": True})
        
        message = data['message']
        chat_id = message['chat']['id']
        user_id = message['from']['id']
        username = message['from'].get('username', f"user_{user_id}")
        full_name = f"{message['from'].get('first_name', '')} {message['from'].get('last_name', '')}".strip()
        
        # Получаем текст сообщения
        text = message.get('text', message.get('caption', ''))
        
        if not text:
            return JsonResponse({"ok": True})
        
        # Получаем фото если есть
        image_data = None
        if 'photo' in message:
            # Берём фото наибольшего размера
            photo = message['photo'][-1]
            file_id = photo['file_id']
            
            telegram = TelegramIntegration()
            image_data = telegram.download_photo(file_id)
        
        # Обрабатываем через единый обработчик
        result = ChannelHandler.process_incoming_message(
            channel=Channel.CHANNEL_TELEGRAM,
            user_identifier=str(user_id),
            text=text,
            image_data=image_data,
            external_id=str(chat_id),
            metadata={
                "username": username,
                "full_name": full_name,
                "chat_id": chat_id,
            }
        )
        
        # Отправляем ответ в Telegram
        telegram = TelegramIntegration()
        telegram.send_message(chat_id, result['reply'])
        
        return JsonResponse({"ok": True})
        
    except Exception as e:
        logger.error(f"Telegram webhook error: {e}")
        return JsonResponse({"error": str(e)}, status=500)
