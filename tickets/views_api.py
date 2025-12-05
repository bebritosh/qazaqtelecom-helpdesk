"""
API endpoints для внешних систем
"""
import json
import base64
from django.http import JsonResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .channel_handler import ChannelHandler
from .models import Channel
import logging

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def external_api_endpoint(request: HttpRequest) -> JsonResponse:
    """
    Универсальный API endpoint для приёма обращений из внешних систем
    
    URL: /tickets/api/external/message/
    
    Request body (JSON):
    {
        "api_key": "your-api-key",  // Ключ для аутентификации
        "user_identifier": "user@example.com",  // Email, username, phone и т.д.
        "text": "Проблема с интернетом",
        "image_base64": "...",  // Опционально: изображение в base64
        "external_id": "external-system-id",  // Опционально
        "metadata": {  // Опционально
            "full_name": "Иванов Иван",
            "email": "user@example.com",
            "phone": "+77001234567"
        }
    }
    
    Response:
    {
        "success": true,
        "ticket_id": 123,
        "reply": "Ответ AI ассистента",
        "needs_escalation": false
    }
    """
    try:
        data = json.loads(request.body)
        
        # Проверяем API ключ
        api_key = data.get('api_key')
        from django.conf import settings
        valid_api_key = getattr(settings, 'EXTERNAL_API_KEY', 'demo-api-key-change-in-production')
        
        if api_key != valid_api_key:
            return JsonResponse({
                "success": False,
                "error": "Invalid API key"
            }, status=401)
        
        # Получаем данные
        user_identifier = data.get('user_identifier')
        text = data.get('text')
        
        if not user_identifier or not text:
            return JsonResponse({
                "success": False,
                "error": "user_identifier and text are required"
            }, status=400)
        
        # Декодируем изображение если есть
        image_data = None
        if 'image_base64' in data:
            try:
                image_data = base64.b64decode(data['image_base64'])
            except Exception as e:
                logger.warning(f"Failed to decode image: {e}")
        
        # Обрабатываем через единый обработчик
        result = ChannelHandler.process_incoming_message(
            channel=Channel.CHANNEL_API,
            user_identifier=user_identifier,
            text=text,
            image_data=image_data,
            external_id=data.get('external_id'),
            metadata=data.get('metadata', {})
        )
        
        return JsonResponse({
            "success": True,
            "ticket_id": result['ticket_id'],
            "reply": result['reply'],
            "needs_escalation": result['needs_escalation'],
            "status": result['status']
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            "success": False,
            "error": "Invalid JSON"
        }, status=400)
    except Exception as e:
        logger.error(f"External API error: {e}")
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def api_status(request: HttpRequest) -> JsonResponse:
    """
    Проверка статуса API
    URL: /tickets/api/status/
    """
    return JsonResponse({
        "status": "ok",
        "version": "1.0",
        "channels": {
            "web": True,
            "email": True,
            "telegram": True,
            "api": True,
        }
    })
