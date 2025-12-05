"""
Views для базы знаний
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpRequest
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Q
import json

from .models import KnowledgeArticle, Ticket
from .knowledge_service import KnowledgeBaseService


def knowledge_base_list(request: HttpRequest):
    """Список всех статей базы знаний"""
    query = request.GET.get("q", "")
    category = request.GET.get("category", "")
    
    articles = KnowledgeArticle.objects.filter(status=KnowledgeArticle.STATUS_PUBLISHED)
    
    if query:
        articles = articles.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(tags__icontains=query)
        )
    
    if category:
        articles = articles.filter(category=category)
    
    articles = articles.order_by("-published_at")
    
    # Популярные статьи
    popular = KnowledgeBaseService.get_popular_articles(limit=5)
    
    # Самые полезные
    helpful = KnowledgeBaseService.get_helpful_articles(limit=5)
    
    context = {
        "articles": articles,
        "popular_articles": popular,
        "helpful_articles": helpful,
        "query": query,
        "category": category,
        "categories": Ticket.CATEGORY_CHOICES,
    }
    
    return render(request, "knowledge/list.html", context)


def knowledge_article_detail(request: HttpRequest, slug: str):
    """Просмотр статьи"""
    article = get_object_or_404(KnowledgeArticle, slug=slug, status=KnowledgeArticle.STATUS_PUBLISHED)
    
    # Увеличиваем счётчик просмотров
    article.increment_views()
    
    # Похожие статьи
    similar = KnowledgeArticle.objects.filter(
        status=KnowledgeArticle.STATUS_PUBLISHED,
        category=article.category
    ).exclude(id=article.id).order_by("-views_count")[:5]
    
    context = {
        "article": article,
        "similar_articles": similar,
    }
    
    return render(request, "knowledge/detail.html", context)


@require_POST
def rate_article(request: HttpRequest, article_id: int):
    """Оценка статьи как полезной или нет"""
    try:
        data = json.loads(request.body)
        is_helpful = data.get("is_helpful", True)
        
        article = get_object_or_404(KnowledgeArticle, id=article_id)
        article.mark_helpful(is_helpful)
        
        return JsonResponse({
            "success": True,
            "helpful_count": article.helpful_count,
            "not_helpful_count": article.not_helpful_count,
            "score": article.helpfulness_score,
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def knowledge_search_api(request: HttpRequest):
    """API для поиска статей (для автокомплита)"""
    query = request.GET.get("q", "")
    category = request.GET.get("category", "")
    
    if len(query) < 2:
        return JsonResponse({"results": []})
    
    articles = KnowledgeBaseService.search_articles(query, category, limit=10)
    
    results = []
    for article in articles:
        results.append({
            "id": article.id,
            "title": article.title,
            "summary": article.summary[:100] + "..." if len(article.summary) > 100 else article.summary,
            "url": f"/knowledge/{article.slug}/",
            "category": article.get_category_display(),
            "views": article.views_count,
            "helpfulness": article.helpfulness_score,
        })
    
    return JsonResponse({"results": results})


@login_required
def create_article_from_ticket(request: HttpRequest, ticket_id: int):
    """Создание статьи из тикета (для операторов)"""
    if not (request.user.is_staff or request.user.role == "operator"):
        return JsonResponse({"error": "Permission denied"}, status=403)
    
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    # Генерируем статью
    article = KnowledgeBaseService.generate_article_from_ticket(ticket, author=request.user)
    
    if article:
        return JsonResponse({
            "success": True,
            "article_id": article.id,
            "redirect_url": f"/knowledge/edit/{article.id}/",
        })
    else:
        return JsonResponse({
            "error": "Не удалось создать статью. Тикет должен быть закрыт и иметь решение."
        }, status=400)


@login_required
def edit_article(request: HttpRequest, article_id: int):
    """Редактирование статьи (Markdown редактор)"""
    if not (request.user.is_staff or request.user.role == "operator"):
        return redirect("knowledge:list")
    
    article = get_object_or_404(KnowledgeArticle, id=article_id)
    
    if request.method == "POST":
        article.title = request.POST.get("title", article.title)
        article.content = request.POST.get("content", article.content)
        article.summary = request.POST.get("summary", article.summary)
        article.tags = request.POST.get("tags", article.tags)
        article.category = request.POST.get("category", article.category)
        article.status = request.POST.get("status", article.status)
        
        # Если публикуем впервые
        if article.status == KnowledgeArticle.STATUS_PUBLISHED and not article.published_at:
            article.published_at = timezone.now()
        
        article.save()
        
        return redirect("knowledge:detail", slug=article.slug)
    
    context = {
        "article": article,
        "categories": Ticket.CATEGORY_CHOICES,
        "statuses": KnowledgeArticle.STATUS_CHOICES,
    }
    
    return render(request, "knowledge/edit.html", context)


@login_required
def suggest_articles_for_ticket(request: HttpRequest, ticket_id: int):
    """API: предлагает статьи для тикета"""
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    similar = KnowledgeBaseService.find_similar_articles(ticket, limit=5)
    
    results = []
    for article in similar:
        results.append({
            "id": article.id,
            "title": article.title,
            "summary": article.summary,
            "url": f"/knowledge/{article.slug}/",
            "helpfulness": article.helpfulness_score,
        })
    
    return JsonResponse({"suggestions": results})
