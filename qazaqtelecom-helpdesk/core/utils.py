from __future__ import annotations

from typing import Any, Dict, List, Optional

from django.conf import settings


class AIService:
    model_name = "gemini-2.5-flash"

    @classmethod
    def _get_model(cls):
        # Проверяем валидность API ключа
        if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY in ["your-gemini-api-key-here", ""]:
            return None
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            return genai.GenerativeModel(cls.model_name)
        except Exception as e:
            print(f"Ошибка инициализации Gemini: {e}")
            return None

    @classmethod
    def classify_ticket(cls, text: str, image: Optional[bytes] = None) -> Dict[str, Any]:
        model = cls._get_model()
        
        # Если API недоступен - возвращаем дефолтные значения
        if model is None:
            return {
                "category": "Internet" if "интернет" in text.lower() or "internet" in text.lower() else "Other",
                "priority": "Medium",
                "department": "Technical",
                "summary": text[:200],
                "router_model": None,
            }
        
        try:
            prompt = (
                "Проанализируй запрос пользователя для службы поддержки Казахтелеком. "
                "Верни ТОЛЬКО валидный JSON без комментариев и лишнего текста в формате: "
                "{\"category\": str, \"priority\": str, \"department\": str, \"summary\": str, \"router_model\": str | null}. "
                "Если на фото есть ошибка роутера — постарайся определить модель роутера в поле router_model."
            )

            contents: List[Any] = [prompt, "\n\nТекст обращения:\n", text]
            if image is not None:
                contents.append({"mime_type": "image/jpeg", "data": image})

            response = model.generate_content(contents)
            import json
            return json.loads(response.text)
        except Exception:
            return {
                "category": "Other",
                "priority": "Medium",
                "department": "Technical",
                "summary": text[:200],
                "router_model": None,
            }

    @classmethod
    def generate_response(
        cls,
        history: List[Dict[str, str]],
        user_input: str,
        language: str = "ru",
    ) -> str:
        model = cls._get_model()
        
        # Если API недоступен - возвращаем заготовленный ответ
        if model is None:
            demo_responses = [
                "Здравствуйте! Я помогу вам решить проблему. Попробуйте перезагрузить роутер: отключите питание на 30 секунд, затем включите обратно.",
                "Понял вашу проблему. Для диагностики мне нужно больше информации. Какая у вас модель роутера?",
                "Спасибо за обращение! Проверьте, пожалуйста, горят ли индикаторы на роутере. Какие из них активны?",
                "Я вижу, что проблема может быть сложной. Перевожу на специалиста для детальной диагностики.",
            ]
            import random
            return random.choice(demo_responses)
        
        try:
            lang = (language or "ru").lower()
            lang_name = "Русский" if lang == "ru" else "Казахский"

            system_prompt = (
                f"Ты виртуальный оператор поддержки Казахтелеком. "
                f"Отвечай строго на языке пользователя. Текущий язык: {lang_name}. "
                "Отвечай кратко, вежливо, без воды, понятным языком для обычного человека (в том числе пожилых клиентов). "
                "ВСЕГДА структурируй ответ в три блока. "
                "Блок 1: заголовок 'Қысқаша:' (для казахского) или 'Кратко:' (для русского) и 1–2 предложения с сутью. "
                "Блок 2: заголовок 'Қадамдар:' / 'Шаги:' и нумерованный список конкретных шагов, что делать. "
                "Блок 3: заголовок 'Егер көмектеспесе:' / 'Если не помогло:' и короткая фраза о том, что заявка будет переведена на специалиста, если проблема сложная. "
                "Если проблема типовая (перезагрузка роутера, проверка кабеля, перезапуск ONT, проверка баланса, смена Wi‑Fi пароля) — давай понятную пошаговую инструкцию. "
                "Если проблема выглядит сложной или требует доступа к внутренним системам — ОБЯЗАТЕЛЬНО добавь фразу 'Перевожу на специалиста'."
            )

            history_lines: List[str] = []
            for msg in history:
                role = "Клиент" if not msg.get("is_bot") else "Бот"
                text = msg.get("text", "").strip()
                if text:
                    history_lines.append(f"{role}: {text}")

            history_block = "\n".join(history_lines) if history_lines else "(нет предыдущих сообщений)"

            prompt = (
                f"{system_prompt}\n\n"
                f"История диалога:\n{history_block}\n\n"
                f"Новое сообщение клиента: {user_input.strip()}\n\n"
                f"Сформулируй ответ для клиента."
            )

            response = model.generate_content(prompt)
            if not hasattr(response, "text"):
                return ""

            text = response.text.strip()
            # Удаляем внешние кавычки, если модель вернула весь ответ в "..." или '...'
            if (text.startswith("\"") and text.endswith("\"")) or (text.startswith("'") and text.endswith("'")):
                text = text[1:-1].strip()

            return text
        except Exception as e:
            print(f"Gemini generate_response error: {e}")
            return "Извините, возникла техническая проблема. Попробуйте переформулировать вопрос или обратитесь к оператору."
