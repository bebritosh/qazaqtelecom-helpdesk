from django.core.management.base import BaseCommand
from django.conf import settings
import google.generativeai as genai
import os

class Command(BaseCommand):
    help = "Test Gemini AI connection"

    def handle(self, *args, **options):
        self.stdout.write("=== AI DIAGNOSTIC ===")
        
        # 1. Проверка переменных окружения
        env_key = os.environ.get('GEMINI_API_KEY')
        settings_key = getattr(settings, 'GEMINI_API_KEY', None)
        
        self.stdout.write(f"Key in os.environ: {'PRESENT' if env_key else 'MISSING'}")
        self.stdout.write(f"Key in settings:   {'PRESENT' if settings_key else 'MISSING'}")
        
        if settings_key:
            masked_key = settings_key[:5] + "..." + settings_key[-5:]
            self.stdout.write(f"Key value:         {masked_key}")
        else:
            self.stdout.write("Key value:         None")

        # 2. Проверка подключения к Gemini
        if not settings_key:
            self.stdout.write(self.style.ERROR("FAIL: No API key found in settings."))
            return

        self.stdout.write("\nTesting connection to Google Gemini...")
        try:
            genai.configure(api_key=settings_key)
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content("Test connection. Reply with 'OK'.")
            
            if response and response.text:
                self.stdout.write(self.style.SUCCESS(f"SUCCESS: Gemini responded: {response.text.strip()}"))
            else:
                self.stdout.write(self.style.WARNING("WARNING: Gemini responded but text is empty."))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"FAIL: Connection failed.\nError: {e}"))
