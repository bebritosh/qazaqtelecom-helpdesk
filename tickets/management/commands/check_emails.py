"""
Management command для проверки и обработки входящих email
Запуск: python manage.py check_emails
"""
from django.core.management.base import BaseCommand
from tickets.integrations.email_integration import EmailIntegration


class Command(BaseCommand):
    help = 'Проверяет и обрабатывает входящие email обращения'

    def handle(self, *args, **options):
        self.stdout.write('Проверка входящих email...')
        
        integration = EmailIntegration()
        processed = integration.fetch_new_emails()
        
        if processed:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Обработано {len(processed)} новых email обращений'
                )
            )
        else:
            self.stdout.write('Новых email обращений не найдено')
