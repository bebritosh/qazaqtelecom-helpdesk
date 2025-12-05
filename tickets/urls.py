from django.urls import path

from . import views
from . import views_chat as chat_views
from . import views_operator as op_views
from . import views_api as api_views
from .integrations.telegram_integration import telegram_webhook

app_name = "tickets"

urlpatterns = [
    path("api/chat/", views.chat_api, name="chat_api"),
    path("api/chat/history/", views.chat_history, name="chat_history"),
    path("api/chat/rate/", views.rate_message, name="rate_message"),
    # External API endpoints
    path("api/external/message/", api_views.external_api_endpoint, name="external_api"),
    path("api/status/", api_views.api_status, name="api_status"),
    # Telegram webhook
    path("api/telegram/webhook/", telegram_webhook, name="telegram_webhook"),
    path("operator/", op_views.operator_ticket_list, name="operator_ticket_list"),
    path("operator/<int:pk>/", op_views.operator_ticket_detail, name="operator_ticket_detail"),
    path("dashboard/", op_views.manager_dashboard, name="dashboard"),
    # Chat endpoints для операторов
    path("api/operator/chat/<int:ticket_id>/join/", chat_views.operator_join_chat, name="operator_join_chat"),
    path("api/operator/chat/<int:ticket_id>/send/", chat_views.operator_send_message, name="operator_send_message"),
    path("api/operator/chat/<int:ticket_id>/messages/", chat_views.get_chat_messages, name="get_chat_messages"),
    path("api/operator/notifications/", chat_views.get_notifications, name="get_notifications"),
    path("operator/chat/<int:ticket_id>/", chat_views.operator_chat_view, name="operator_chat"),
]
