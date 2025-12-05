from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from tickets.models import Message, Ticket


class Command(BaseCommand):
    help = "Create initial demo data: admin user, operator, sample tickets"

    def handle(self, *args, **options):
        User = get_user_model()

        if not User.objects.filter(username="admin").exists():
            self.stdout.write("Creating admin user admin/admin")
            User.objects.create_superuser(
                username="admin",
                password="admin",
                full_name="Admin",
            )

        operator, _ = User.objects.get_or_create(
            username="operator",
            defaults={
                "full_name": "Operator",
                "role": User.ROLE_OPERATOR,
            },
        )
        operator.set_password("operator")
        operator.save()

        client, _ = User.objects.get_or_create(
            username="client",
            defaults={
                "full_name": "Demo Client",
                "role": User.ROLE_CLIENT,
            },
        )
        client.set_password("client")
        client.save()

        if not Ticket.objects.exists():
            t1 = Ticket.objects.create(
                author=client,
                subject="Низкая скорость интернета",
                description="Интернет тормозит вечером",
                category=Ticket.CATEGORY_INTERNET,
                priority=Ticket.PRIORITY_HIGH,
                department=Ticket.DEPT_TECHNICAL,
                is_auto_solved=False,
            )
            Message.objects.create(ticket=t1, text="Интернет очень медленный", is_bot=False)

            t2 = Ticket.objects.create(
                author=client,
                subject="Вопрос по оплате",
                description="Не могу посмотреть баланс",
                category=Ticket.CATEGORY_BILLING,
                priority=Ticket.PRIORITY_MEDIUM,
                department=Ticket.DEPT_FINANCIAL,
                is_auto_solved=True,
            )
            Message.objects.create(ticket=t2, text="Как узнать баланс?", is_bot=False)
            Message.objects.create(ticket=t2, text="Вы можете проверить баланс в личном кабинете.", is_bot=True)

        self.stdout.write(self.style.SUCCESS("Initial data created/updated."))
