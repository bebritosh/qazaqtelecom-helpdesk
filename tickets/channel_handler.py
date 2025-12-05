"""
Универсальный обработчик входящих сообщений из разных каналов
"""
from typing import Dict, Any, Optional
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from .models import Ticket, Message, Channel
from core.utils import AIService
import base64

User = get_user_model()


class ChannelHandler:
    """Единая точка входа для обработки сообщений из всех каналов"""
    
    @staticmethod
    def process_incoming_message(
        channel: str,
        user_identifier: str,  # email, telegram_id, phone, username
        text: str,
        image_data: Optional[bytes] = None,
        external_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Обрабатывает входящее сообщение из любого канала
        
        Args:
            channel: Канал коммуникации (web, email, telegram, whatsapp, api)
            user_identifier: Идентификатор пользователя (email, telegram_id и т.д.)
            text: Текст сообщения
            image_data: Бинарные данные изображения (опционально)
            external_id: ID сообщения во внешней системе
            metadata: Дополнительные метаданные
            
        Returns:
            Dict с ответом AI и информацией о тикете
        """
        metadata = metadata or {}
        
        # Получаем или создаём пользователя
        user = ChannelHandler._get_or_create_user(channel, user_identifier, metadata)
        
        # Получаем или создаём тикет
        ticket = ChannelHandler._get_or_create_ticket(
            user=user,
            channel=channel,
            external_id=external_id,
            text=text,
            image_data=image_data
        )
        
        # Сохраняем сообщение пользователя
        user_message = Message.objects.create(
            ticket=ticket,
            text=text,
            is_bot=False,
            sender=user,
        )
        
        if image_data:
            user_message.image.save(
                f"message_{user_message.id}.jpg",
                ContentFile(image_data),
                save=True
            )
        
        # Получаем историю для контекста
        history = []
        for msg in ticket.messages.order_by("created_at"):
            history.append({
                "text": msg.text,
                "is_bot": msg.is_bot,
            })
        
        # Генерируем ответ AI
        language = getattr(user, 'language', 'ru')
        ai_response = AIService.generate_response(
            history=history,
            user_input=text,
            language=language
        )
        
        # Сохраняем ответ AI (от имени системы, без конкретного пользователя)
        bot_message = Message.objects.create(
            ticket=ticket,
            text=ai_response,
            is_bot=True,
            sender=None,
        )
        
        # Проверяем необходимость эскалации
        needs_escalation = any(phrase in ai_response.lower() for phrase in [
            "перевожу на специалиста",
            "перевожу на оператора",
            "передам специалисту",
            "свяжу со специалистом"
        ])
        
        if needs_escalation and ticket.status == Ticket.STATUS_NEW:
            ticket.status = Ticket.STATUS_IN_PROGRESS
            ticket.is_auto_solved = False
            ticket.save(update_fields=["status", "is_auto_solved"])
        
        return {
            "reply": ai_response,
            "ticket_id": ticket.id,
            "channel": channel,
            "needs_escalation": needs_escalation,
            "status": ticket.status
        }
    
    @staticmethod
    def _get_or_create_user(channel: str, identifier: str, metadata: Dict) -> User:
        """Получает существующего пользователя или создаёт нового"""
        
        # Для веб-канала пользователь уже авторизован
        if channel == Channel.CHANNEL_WEB:
            # Предполагаем, что identifier это username
            return User.objects.get(username=identifier)
        
        # Для email ищем по email
        if channel == Channel.CHANNEL_EMAIL:
            user, created = User.objects.get_or_create(
                email=identifier,
                defaults={
                    "username": identifier.split("@")[0],
                    "full_name": metadata.get("full_name", identifier),
                }
            )
            return user
        
        # Для Telegram/WhatsApp создаём пользователя с уникальным username
        if channel in [Channel.CHANNEL_TELEGRAM, Channel.CHANNEL_WHATSAPP]:
            username = f"{channel}_{identifier}"
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "full_name": metadata.get("full_name", identifier),
                    "phone": metadata.get("phone", ""),
                }
            )
            return user
        
        # Для API ищем по username или email
        user, created = User.objects.get_or_create(
            username=identifier,
            defaults={
                "email": metadata.get("email", ""),
                "full_name": metadata.get("full_name", identifier),
            }
        )
        return user
    
    @staticmethod
    def _get_or_create_ticket(
        user: User,
        channel: str,
        external_id: Optional[str],
        text: str,
        image_data: Optional[bytes]
    ) -> Ticket:
        """Получает существующий открытый тикет или создаёт новый"""
        
        # Ищем открытый тикет пользователя из этого канала
        open_ticket = Ticket.objects.filter(
            author=user,
            channel=channel,
            status__in=[Ticket.STATUS_NEW, Ticket.STATUS_IN_PROGRESS]
        ).first()
        
        if open_ticket:
            return open_ticket
        
        # Классифицируем новый тикет
        classification = AIService.classify_ticket(text, image_data)
        
        # Создаём новый тикет
        ticket = Ticket.objects.create(
            author=user,
            channel=channel,
            external_id=external_id,
            subject=classification.get("summary", text[:100]),
            description=text,
            category=classification.get("category", "other").lower(),
            priority=classification.get("priority", "medium").lower(),
            department=classification.get("department", "technical").lower(),
        )
        
        return ticket
