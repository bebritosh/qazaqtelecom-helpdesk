from __future__ import annotations

from typing import Dict, List

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_POST

from core.utils import AIService

from .models import Message, Ticket


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

    if "Перевожу на специалиста" in (reply or ""):
        ticket.status = Ticket.STATUS_IN_PROGRESS
        ticket.is_auto_solved = False
    else:
        ticket.is_auto_solved = True
    ticket.save(update_fields=["status", "is_auto_solved"])

    return JsonResponse({"reply": bot_message.text})
