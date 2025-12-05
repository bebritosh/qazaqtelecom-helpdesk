"""
URLs для базы знаний
"""
from django.urls import path
from . import views_knowledge

app_name = "knowledge"

urlpatterns = [
    # Публичные страницы
    path("", views_knowledge.knowledge_base_list, name="list"),
    # Используем str-конвертер, чтобы поддерживать Unicode-слиги (в том числе кириллицу)
    path("<str:slug>/", views_knowledge.knowledge_article_detail, name="detail"),
    
    # API
    path("api/search/", views_knowledge.knowledge_search_api, name="search_api"),
    path("api/rate/<int:article_id>/", views_knowledge.rate_article, name="rate"),
    path("api/suggest/<int:ticket_id>/", views_knowledge.suggest_articles_for_ticket, name="suggest"),
    
    # Для операторов
    path("create-from-ticket/<int:ticket_id>/", views_knowledge.create_article_from_ticket, name="create_from_ticket"),
    path("edit/<int:article_id>/", views_knowledge.edit_article, name="edit"),
]
