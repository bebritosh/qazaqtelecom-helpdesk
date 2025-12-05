from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Ticket',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('new', 'New'), ('in_progress', 'In progress'), ('closed', 'Closed')], default='new', max_length=20)),
                ('priority', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], default='medium', max_length=20)),
                ('category', models.CharField(choices=[('internet', 'Internet'), ('tv', 'TV'), ('billing', 'Billing'), ('other', 'Other')], default='other', max_length=20)),
                ('department', models.CharField(choices=[('technical', 'Technical'), ('financial', 'Financial'), ('sales', 'Sales')], default='technical', max_length=20)),
                ('subject', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('is_auto_solved', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tickets', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField(blank=True)),
                ('image', models.ImageField(blank=True, null=True, upload_to='ticket_images/')),
                ('is_bot', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('ticket', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='tickets.ticket')),
            ],
        ),
    ]
