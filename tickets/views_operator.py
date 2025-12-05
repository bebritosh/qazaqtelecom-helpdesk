from __future__ import annotations

from datetime import timedelta

from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Avg, Count, Min, Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from core.utils import AIService

from .models import Ticket


def _is_operator(user) -> bool:
    from core.models import User

    if not user.is_authenticated:
        return False

    # Операторская зона доступна:
    # - пользователям с ролью operator/admin
    # - всем сотрудникам (is_staff) и суперпользователям
    return user.role in {User.ROLE_OPERATOR, User.ROLE_ADMIN} or user.is_staff or user.is_superuser


operator_required = user_passes_test(_is_operator)


@login_required
@operator_required
def operator_ticket_list(request: HttpRequest) -> HttpResponse:
    tickets = (
        Ticket.objects.filter(is_auto_solved=False)
        .filter(Q(status=Ticket.STATUS_NEW) | Q(status=Ticket.STATUS_IN_PROGRESS))
        .select_related("author")
        .order_by("-created_at")
    )
    return render(request, "tickets/operator_ticket_list.html", {"tickets": tickets})


@login_required
@operator_required
def operator_ticket_detail(request: HttpRequest, pk: int) -> HttpResponse:
    ticket = get_object_or_404(Ticket.objects.select_related("author"), pk=pk)

    if request.method == "POST" and "generate_ai_reply" in request.POST:
        history = [
            {"text": m.text, "is_bot": m.is_bot}
            for m in ticket.messages.order_by("created_at")
        ]
        user_input = request.POST.get("operator_note", "")
        language = getattr(request.user, "language", "ru") or "ru"
        ai_suggestion = AIService.generate_response(history=history, user_input=user_input, language=language)
        return render(
            request,
            "tickets/operator_ticket_detail.html",
            {"ticket": ticket, "ai_suggestion": ai_suggestion},
        )

    return render(request, "tickets/operator_ticket_detail.html", {"ticket": ticket})


@login_required
@operator_required
def manager_dashboard(request: HttpRequest) -> HttpResponse:
    total_tickets = Ticket.objects.count()
    by_category = (
        Ticket.objects.values("category")
        .annotate(count=Count("id"))
        .order_by("category")
    )
    auto_solved = Ticket.objects.filter(is_auto_solved=True).count()
    auto_solved_percent = (auto_solved / total_tickets * 100) if total_tickets else 0

    from .models import Message

    first_bot_times = (
        Message.objects.filter(is_bot=True)
        .values("ticket_id")
        .annotate(first_bot=Min("created_at"))
    )
    diffs = []
    for row in first_bot_times:
        try:
            t = Ticket.objects.get(id=row["ticket_id"])
            diffs.append(row["first_bot"] - t.created_at)
        except Ticket.DoesNotExist:
            continue
    if diffs:
        avg_seconds = sum((d.total_seconds() for d in diffs)) / len(diffs)
    else:
        avg_seconds = 0

    context = {
        "total_tickets": total_tickets,
        "auto_solved_percent": round(auto_solved_percent, 1),
        "by_category": list(by_category),
        "avg_response_time_seconds": int(avg_seconds),
    }
    return render(request, "tickets/dashboard.html", context)
