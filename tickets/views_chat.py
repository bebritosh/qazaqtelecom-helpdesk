"""Views для работы операторов с чатами пользователей"""
from __future__ import annotations

from typing import Dict, List

from django.contrib.auth.decorators import login_required
from django.db import models
from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Message, Notification, Ticket


@login_required
@require_POST
def operator_join_chat(request: HttpRequest, ticket_id: int) -> JsonResponse:
    """Оператор присоединяется к чату с пользователем"""
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    # Проверяем, что пользователь - оператор или админ
    if not (request.user.is_staff or request.user.role == 'operator'):
        return JsonResponse({"error": "Access denied"}, status=403)
    
    # Назначаем оператора на тикет
    if not ticket.assigned_operator:
        ticket.assigned_operator = request.user
    
    ticket.operator_joined = True
    ticket.save(update_fields=["assigned_operator", "operator_joined"])
    
    # Помечаем уведомления как прочитанные
    Notification.objects.filter(
        operator=request.user,
        ticket=ticket,
        is_read=False
    ).update(is_read=True)
    
    return JsonResponse({"success": True})


@login_required
@require_POST
def operator_send_message(request: HttpRequest, ticket_id: int) -> JsonResponse:
    """Оператор отправляет сообщение в чат пользователя"""
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    # Проверяем, что пользователь - оператор или админ
    if not (request.user.is_staff or request.user.role == 'operator'):
        return JsonResponse({"error": "Access denied"}, status=403)
    
    text = request.POST.get("text", "").strip()
    if not text:
        return JsonResponse({"error": "Empty message"}, status=400)
    
    # Создаём сообщение от оператора
    message = Message.objects.create(
        ticket=ticket,
        text=text,
        is_bot=False,
        sender=request.user,
    )
    
    # Обновляем статус тикета
    if ticket.status == Ticket.STATUS_NEW:
        ticket.status = Ticket.STATUS_IN_PROGRESS
        ticket.save(update_fields=["status"])
    
    return JsonResponse({
        "success": True,
        "message": {
            "id": message.id,
            "text": message.text,
            "created_at": message.created_at.isoformat(),
            "sender": request.user.username,
        }
    })


@login_required
def operator_chat_view(request: HttpRequest, ticket_id: int):
    """Страница чата оператора с пользователем"""
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    # Проверяем, что пользователь - оператор или админ
    if not (request.user.is_staff or request.user.role == 'operator'):
        return JsonResponse({"error": "Access denied"}, status=403)
    
    # Получаем все сообщения
    messages = ticket.messages.select_related('sender').order_by('created_at')
    
    # Помечаем уведомления как прочитанные
    Notification.objects.filter(
        operator=request.user,
        ticket=ticket,
        is_read=False
    ).update(is_read=True)
    
    return render(request, "tickets/operator_chat.html", {
        "ticket": ticket,
        "messages": messages,
    })


@login_required
def get_chat_messages(request: HttpRequest, ticket_id: int) -> JsonResponse:
    """API для получения сообщений чата (для обновления в реальном времени)"""
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    # Проверяем доступ: либо автор тикета, либо оператор/админ
    is_author = ticket.author == request.user
    is_operator = request.user.is_staff or request.user.role == 'operator'
    
    if not (is_author or is_operator):
        return JsonResponse({"error": "Access denied"}, status=403)
    
    messages = ticket.messages.select_related('sender').order_by('created_at')
    
    messages_data = []
    for msg in messages:
        sender_name = "AI"
        if msg.sender:
            sender_name = msg.sender.username
        elif not msg.is_bot:
            sender_name = ticket.author.username
        
        messages_data.append({
            "id": msg.id,
            "text": msg.text,
            "is_bot": msg.is_bot,
            "sender": sender_name,
            "created_at": msg.created_at.isoformat(),
        })
    
    return JsonResponse({
        "messages": messages_data,
        "operator_joined": ticket.operator_joined,
        "assigned_operator": ticket.assigned_operator.username if ticket.assigned_operator else None,
    })


@login_required
def get_notifications(request: HttpRequest) -> JsonResponse:
    """API для получения уведомлений оператора"""
    if not (request.user.is_staff or request.user.role == 'operator'):
        return JsonResponse({"error": "Access denied"}, status=403)
    
    notifications = Notification.objects.filter(
        operator=request.user,
        is_read=False
    ).select_related('ticket')[:10]
    
    notifications_data = []
    for notif in notifications:
        notifications_data.append({
            "id": notif.id,
            "message": notif.message,
            "ticket_id": notif.ticket.id,
            "ticket_subject": notif.ticket.subject,
            "created_at": notif.created_at.isoformat(),
        })
    
    return JsonResponse({
        "notifications": notifications_data,
        "unread_count": notifications.count(),
    })
