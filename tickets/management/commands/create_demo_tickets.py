from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models import User
from tickets.models import Ticket, Message


class Command(BaseCommand):
    help = "Создаёт демо-тикеты и сообщения для презентации"

    def handle(self, *args, **options):
        # Получаем пользователей
        try:
            client = User.objects.get(username='client')
            operator = User.objects.get(username='operator')
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('Пользователи client/operator не найдены. Запустите create_init_data'))
            return

        # Удаляем старые демо-тикеты
        Ticket.objects.all().delete()

        # Создаём тикеты
        tickets_data = [
            {
                'subject': 'Низкая скорость интернета вечером',
                'description': 'У меня очень низкая скорость интернета по вечерам, днём всё нормально.',
                'category': 'internet',
                'priority': 'high',
                'department': 'technical',
                'status': 'new',
                'is_auto_solved': False,
                'messages': [
                    {'text': 'Добрый день! У меня очень низкая скорость интернета по вечерам, днём всё нормально. Что делать?', 'is_bot': False},
                    {'text': 'Здравствуйте! Проверьте, пожалуйста, сколько устройств подключено к роутеру вечером. Также попробуйте перезагрузить роутер.', 'is_bot': True},
                ]
            },
            {
                'subject': 'Не работает Wi-Fi на телефоне',
                'description': 'Wi-Fi не подключается на телефоне, пишет "Неверный пароль"',
                'category': 'internet',
                'priority': 'medium',
                'department': 'technical',
                'status': 'in_progress',
                'is_auto_solved': False,
                'messages': [
                    {'text': 'Wi-Fi не подключается на телефоне, пишет "Неверный пароль", хотя пароль правильный', 'is_bot': False},
                    {'text': 'Попробуйте "забыть" сеть на телефоне и подключиться заново. Также проверьте, нет ли русских букв в пароле.', 'is_bot': True},
                    {'text': 'Спасибо, помогло! Оказалось, была включена русская раскладка', 'is_bot': False},
                ]
            },
            {
                'subject': 'Вопрос по тарифу',
                'description': 'Как узнать свой текущий тариф?',
                'category': 'billing',
                'priority': 'low',
                'department': 'financial',
                'status': 'closed',
                'is_auto_solved': True,
                'messages': [
                    {'text': 'Как узнать свой текущий тариф?', 'is_bot': False},
                    {'text': 'Вы можете узнать свой тариф в личном кабинете на сайте или позвонив по номеру 123.', 'is_bot': True},
                ]
            },
            {
                'subject': 'Пропадает интернет каждые 10 минут',
                'description': 'Интернет пропадает каждые 10-15 минут, потом сам восстанавливается',
                'category': 'internet',
                'priority': 'high',
                'department': 'technical',
                'status': 'new',
                'is_auto_solved': False,
                'messages': [
                    {'text': 'Интернет пропадает каждые 10-15 минут, потом сам восстанавливается. Роутер перезагружал — не помогло.', 'is_bot': False},
                    {'text': 'Это может быть проблема с кабелем или оборудованием провайдера. Перевожу на специалиста для диагностики линии.', 'is_bot': True},
                ]
            },
            {
                'subject': 'Как сменить пароль Wi-Fi',
                'description': 'Подскажите, как поменять пароль от Wi-Fi?',
                'category': 'internet',
                'priority': 'low',
                'department': 'technical',
                'status': 'closed',
                'is_auto_solved': True,
                'messages': [
                    {'text': 'Подскажите, как поменять пароль от Wi-Fi?', 'is_bot': False},
                    {'text': 'Зайдите в настройки роутера по адресу 192.168.1.1, логин/пароль обычно admin/admin. В разделе Wi-Fi найдите поле "Пароль" и измените его.', 'is_bot': True},
                ]
            },
        ]

        for idx, ticket_data in enumerate(tickets_data, 1):
            messages_data = ticket_data.pop('messages')
            
            ticket = Ticket.objects.create(
                author=client,
                **ticket_data,
                created_at=timezone.now() - timedelta(days=5-idx)
            )

            for msg_idx, msg_data in enumerate(messages_data):
                Message.objects.create(
                    ticket=ticket,
                    **msg_data,
                    created_at=ticket.created_at + timedelta(minutes=msg_idx*5)
                )

        self.stdout.write(self.style.SUCCESS(f'Создано {len(tickets_data)} демо-тикетов'))
