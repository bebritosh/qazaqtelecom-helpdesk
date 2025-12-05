"""
Сервис для работы с базой знаний
"""
from typing import List, Dict, Optional
from django.utils.text import slugify
from django.utils import timezone
from django.db.models import Q
from .models import Ticket, KnowledgeArticle, Message
from core.utils import AIService
import re


class KnowledgeBaseService:
    """Сервис для управления базой знаний"""
    
    @staticmethod
    def generate_article_from_ticket(ticket: Ticket, author=None) -> Optional[KnowledgeArticle]:
        """
        Автоматически генерирует статью базы знаний из решённого тикета
        
        Args:
            ticket: Тикет с решённой проблемой
            author: Автор статьи (оператор)
            
        Returns:
            KnowledgeArticle или None если не удалось создать
        """
        # Проверяем, что тикет решён
        if ticket.status != Ticket.STATUS_CLOSED or not ticket.is_auto_solved:
            return None
        
        # Собираем историю диалога
        messages = ticket.messages.order_by("created_at")
        if messages.count() < 2:  # Минимум вопрос + ответ
            return None
        
        # Формируем контекст для AI
        conversation = []
        for msg in messages:
            role = "Клиент" if not msg.is_bot else "AI"
            conversation.append(f"{role}: {msg.text}")
        
        conversation_text = "\n".join(conversation)
        
        # Генерируем статью через AI
        prompt = f"""
На основе этого диалога создай статью для базы знаний в формате Markdown.

Диалог:
{conversation_text}

Создай статью со следующей структурой:

# Заголовок (краткое описание проблемы)

## Проблема
Описание проблемы клиента

## Решение
Пошаговая инструкция решения

## Дополнительно
Полезные советы и рекомендации

Используй Markdown форматирование: заголовки, списки, код блоки.
Пиши понятным языком для обычных пользователей.
"""
        
        try:
            # Генерируем содержание статьи
            article_content = AIService._get_model().generate_content(prompt).text
            
            # Извлекаем заголовок (первая строка с #)
            title_match = re.search(r'^#\s+(.+)$', article_content, re.MULTILINE)
            title = title_match.group(1) if title_match else ticket.subject
            
            # Генерируем краткое описание
            summary = ticket.description[:200] + "..." if len(ticket.description) > 200 else ticket.description
            
            # Создаём slug
            slug = slugify(title, allow_unicode=True)
            # Добавляем ID тикета для уникальности
            slug = f"{slug}-{ticket.id}"
            
            # Извлекаем теги из категории и описания
            tags = [ticket.get_category_display()]
            # Добавляем ключевые слова из описания
            keywords = ["интернет", "роутер", "телевидение", "счет", "скорость", "настройка"]
            for keyword in keywords:
                if keyword in ticket.description.lower():
                    tags.append(keyword)
            
            # Создаём статью
            article = KnowledgeArticle.objects.create(
                title=title,
                slug=slug,
                content=article_content,
                summary=summary,
                category=ticket.category,
                tags=", ".join(tags),
                status=KnowledgeArticle.STATUS_DRAFT,  # Черновик для проверки
                source_ticket=ticket,
                author=author,
            )
            
            return article
            
        except Exception as e:
            print(f"Error generating article: {e}")
            return None
    
    @staticmethod
    def search_articles(
        query: str,
        category: Optional[str] = None,
        status: str = KnowledgeArticle.STATUS_PUBLISHED,
        limit: int = 10
    ) -> List[KnowledgeArticle]:
        """
        Поиск статей в базе знаний
        
        Args:
            query: Поисковый запрос
            category: Фильтр по категории
            status: Статус статей (по умолчанию только опубликованные)
            limit: Максимальное количество результатов
            
        Returns:
            Список найденных статей
        """
        articles = KnowledgeArticle.objects.filter(status=status)
        
        if category:
            articles = articles.filter(category=category)
        
        if query:
            # Поиск по заголовку, содержанию, тегам
            articles = articles.filter(
                Q(title__icontains=query) |
                Q(content__icontains=query) |
                Q(summary__icontains=query) |
                Q(tags__icontains=query)
            )
        
        return articles.order_by("-views_count", "-helpful_count")[:limit]
    
    @staticmethod
    def find_similar_articles(ticket: Ticket, limit: int = 5) -> List[KnowledgeArticle]:
        """
        Находит похожие статьи для тикета
        
        Args:
            ticket: Тикет для которого ищем решения
            limit: Максимальное количество результатов
            
        Returns:
            Список похожих статей
        """
        # Ищем по категории и ключевым словам
        keywords = ticket.description.lower().split()[:10]  # Первые 10 слов
        
        articles = KnowledgeArticle.objects.filter(
            status=KnowledgeArticle.STATUS_PUBLISHED,
            category=ticket.category
        )
        
        # Ищем по ключевым словам
        query = Q()
        for keyword in keywords:
            if len(keyword) > 3:  # Только слова длиннее 3 символов
                query |= Q(title__icontains=keyword) | Q(content__icontains=keyword)
        
        if query:
            articles = articles.filter(query)
        
        # Сортируем по полезности и просмотрам
        return articles.order_by("-helpful_count", "-views_count")[:limit]
    
    @staticmethod
    def get_popular_articles(category: Optional[str] = None, limit: int = 10) -> List[KnowledgeArticle]:
        """Возвращает популярные статьи"""
        articles = KnowledgeArticle.objects.filter(status=KnowledgeArticle.STATUS_PUBLISHED)
        
        if category:
            articles = articles.filter(category=category)
        
        return articles.order_by("-views_count")[:limit]
    
    @staticmethod
    def get_helpful_articles(category: Optional[str] = None, limit: int = 10) -> List[KnowledgeArticle]:
        """Возвращает самые полезные статьи"""
        articles = KnowledgeArticle.objects.filter(
            status=KnowledgeArticle.STATUS_PUBLISHED,
            helpful_count__gt=0
        )
        
        if category:
            articles = articles.filter(category=category)
        
        # Сортируем по проценту полезности
        return sorted(articles, key=lambda x: x.helpfulness_score, reverse=True)[:limit]
    
    @staticmethod
    def suggest_articles_for_user_query(query: str, limit: int = 3) -> List[Dict]:
        """
        Предлагает статьи базы знаний для запроса пользователя
        
        Args:
            query: Запрос пользователя
            limit: Количество предложений
            
        Returns:
            Список словарей с информацией о статьях
        """
        articles = KnowledgeBaseService.search_articles(query, limit=limit)
        
        result = []
        for article in articles:
            result.append({
                "id": article.id,
                "title": article.title,
                "summary": article.summary,
                "url": f"/knowledge/{article.slug}/",
                "helpfulness": article.helpfulness_score,
                "views": article.views_count,
            })
        
        return result
