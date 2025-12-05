from django.urls import path

from . import views
from . import views_operator as op_views

app_name = "tickets"

urlpatterns = [
    path("api/chat/", views.chat_api, name="chat_api"),
    path("operator/", op_views.operator_ticket_list, name="operator_ticket_list"),
    path("operator/<int:pk>/", op_views.operator_ticket_detail, name="operator_ticket_detail"),
    path("dashboard/", op_views.manager_dashboard, name="dashboard"),
]
