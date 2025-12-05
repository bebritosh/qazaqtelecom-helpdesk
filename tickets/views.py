from __future__ import annotations

from typing import Dict, List

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, JsonResponse
from django.db import models

from .models import Ticket, Message, Notification, Channel
from core.utils import AIService
from .channel_handler import ChannelHandler
from django.views.decorators.http import require_POST

from core.models import User
from core.utils import AIService

from django.utils import timezone


def _map_category(raw: str) -> str:
    raw_l = (raw or "").strip().lower()
    if "internet" in raw_l or "интернет" in raw_l:
        return Ticket.CATEGORY_INTERNET
    if "tv" in raw_l or "телевид" in raw_l:
        return Ticket.CATEGORY_TV
    if "bill" in raw_l or "оплат" in raw_l:
        return Ticket.CATEGORY_BILLING
    return Ticket.CATEGORY_OTHER


def _map_priority(raw: str) -> str:
    raw_l = (raw or "").strip().lower()
    if "high" in raw_l or "выс" in raw_l:
        return Ticket.PRIORITY_HIGH
    if "low" in raw_l or "низ" in raw_l:
        return Ticket.PRIORITY_LOW
    return Ticket.PRIORITY_MEDIUM


def _map_department(raw: str) -> str:
    raw_l = (raw or "").strip().lower()
    if "tech" in raw_l or "тех" in raw_l:
        return Ticket.DEPT_TECHNICAL
    if "fin" in raw_l or "фин" in raw_l:
        return Ticket.DEPT_FINANCIAL
    if "sale" in raw_l or "прод" in raw_l:
        return Ticket.DEPT_SALES
    return Ticket.DEPT_TECHNICAL


@login_required
@require_POST
def chat_api(request: HttpRequest) -> JsonResponse:
    text: str = request.POST.get("text", "").strip()
    image_file = request.FILES.get("image")

    if not text and not image_file:
        return JsonResponse({"error": "empty"}, status=400)

    ticket_id = request.session.get("current_ticket_id")
    ticket: Ticket | None = None

    if ticket_id:
        try:
            ticket = Ticket.objects.get(id=ticket_id, author=request.user)
        except Ticket.DoesNotExist:
            ticket = None

    is_new_ticket = False
    if ticket is None:
        ticket = Ticket.objects.create(
            author=request.user,
            subject=text[:120] or "Обращение в поддержку",
            description=text,
        )
        request.session["current_ticket_id"] = ticket.id
        is_new_ticket = True

    user_message = Message.objects.create(
        ticket=ticket,
        text=text,
        image=image_file if image_file else None,
        is_bot=False,
        sender=request.user,
    )

    if is_new_ticket:
        image_bytes = None
        if image_file:
            image_bytes = image_file.read()
        ai_result = AIService.classify_ticket(text=text, image=image_bytes)
        ticket.category = _map_category(ai_result.get("category"))
        ticket.priority = _map_priority(ai_result.get("priority"))
        ticket.department = _map_department(ai_result.get("department"))
        ticket.description = ai_result.get("summary") or ticket.description
        ticket.save(update_fields=["category", "priority", "department", "description"])

    history: List[Dict[str, str]] = []
    for msg in ticket.messages.order_by("created_at"):
        history.append({
            "text": msg.text,
            "is_bot": msg.is_bot,
        })

    language = getattr(request.user, "language", "ru") or "ru"
    reply = AIService.generate_response(history=history, user_input=text, language=language)

    bot_message = Message.objects.create(
        ticket=ticket,
        text=reply or "",
        is_bot=True,
    )

    # Проверяем, нужна ли эскалация
    needs_escalation = any(phrase in (reply or "") for phrase in [
        "Перевожу на специалиста",
        "Перевожу на оператора",
        "передам специалисту",
        "свяжу со специалистом"
    ])
    
    if needs_escalation and not ticket.escalated_at:
        # Эскалация: назначаем оператора и создаём уведомление
        ticket.status = Ticket.STATUS_IN_PROGRESS
        ticket.is_auto_solved = False
        ticket.escalated_at = timezone.now()
        
        # Находим доступного оператора (с ролью operator или staff)
        available_operator = User.objects.filter(
            models.Q(role=User.ROLE_OPERATOR) | models.Q(is_staff=True)
        ).first()
        
        if available_operator:
            ticket.assigned_operator = available_operator
            
            # Создаём уведомление для оператора
            language = getattr(request.user, "language", "ru") or "ru"
            if language == "kk":
                notification_text = f"Жаңа эскалация: {ticket.subject[:50]}"
            else:
                notification_text = f"Новая эскалация: {ticket.subject[:50]}"
            
            Notification.objects.create(
                operator=available_operator,
                ticket=ticket,
                message=notification_text,
            )
        
        ticket.save(update_fields=["status", "is_auto_solved", "escalated_at", "assigned_operator"])
    elif not needs_escalation:
        ticket.is_auto_solved = True
        ticket.save(update_fields=["is_auto_solved"])

    return JsonResponse({
        "reply": bot_message.text,
        "message_id": bot_message.id
    })


@login_required
def chat_history(request: HttpRequest) -> JsonResponse:
    """API для получения истории сообщений текущего тикета пользователя"""
    ticket_id = request.session.get("current_ticket_id")
    
    if not ticket_id:
        return JsonResponse({"messages": []})
    
    try:
        ticket = Ticket.objects.get(id=ticket_id, author=request.user)
    except Ticket.DoesNotExist:
        return JsonResponse({"messages": []})
    
    messages = []
    for msg in ticket.messages.order_by("created_at"):
        messages.append({
            "id": msg.id,
            "text": msg.text,
            "is_bot": msg.is_bot,
            "image_url": msg.image.url if msg.image else None,
            "rating": msg.rating,
        })
    
    return JsonResponse({"messages": messages})


@login_required
@require_POST
def rate_message(request: HttpRequest) -> JsonResponse:
    """API для оценки ответа AI"""
    import json
    try:
        data = json.loads(request.body)
        message_id = data.get("message_id")
        rating = data.get("rating")  # 1 или -1
        
        if not message_id or rating not in [1, -1]:
            return JsonResponse({"error": "Invalid data"}, status=400)
        
        message = Message.objects.get(id=message_id, ticket__author=request.user, is_bot=True)
        message.rating = rating
        message.save(update_fields=["rating"])
        
        return JsonResponse({"success": True, "rating": rating})
    except Message.DoesNotExist:
        return JsonResponse({"error": "Message not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
