import os
import sys
import time
import json
from typing import Optional

import requests
from dotenv import load_dotenv


# Инициализируем Django окружение
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ai_helpdesk.settings")
load_dotenv(os.path.join(BASE_DIR, ".env"))

import django  # noqa: E402

django.setup()  # noqa: E402

from tickets.channel_handler import ChannelHandler  # noqa: E402
from tickets.models import Channel  # noqa: E402


BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    print("[ERROR] TELEGRAM_BOT_TOKEN не задан в .env")
    sys.exit(1)

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"


def get_updates(offset: Optional[int] = None):
    params = {
        "timeout": 30,
    }
    if offset is not None:
        params["offset"] = offset

    try:
        resp = requests.get(f"{API_URL}/getUpdates", params=params, timeout=35)
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            print("[WARN] getUpdates not ok:", data)
            return []
        return data.get("result", [])
    except Exception as e:
        print(f"[ERROR] getUpdates failed: {e}")
        return []


def send_message(chat_id: int, text: str):
    try:
        resp = requests.post(
            f"{API_URL}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text,
            },
            timeout=10,
        )
        if resp.status_code != 200:
            print("[WARN] sendMessage status != 200:", resp.status_code, resp.text)
    except Exception as e:
        print(f"[ERROR] sendMessage failed: {e}")


def main():
    print("[INFO] Telegram polling запущен. Нажмите Ctrl+C для остановки.")
    last_update_id: Optional[int] = None

    while True:
        updates = get_updates(offset=last_update_id + 1 if last_update_id else None)
        for upd in updates:
            last_update_id = upd["update_id"]

            message = upd.get("message") or upd.get("edited_message")
            if not message:
                continue

            chat = message.get("chat", {})
            chat_id = chat.get("id")
            from_user = message.get("from", {})
            user_id = from_user.get("id")
            username = from_user.get("username", f"user_{user_id}")
            first_name = from_user.get("first_name", "")
            last_name = from_user.get("last_name", "")
            full_name = f"{first_name} {last_name}".strip() or username

            text = message.get("text") or message.get("caption")
            if not text:
                continue

            print(f"[INFO] Новое сообщение от {username} ({user_id}): {text}")

            # Пока без поддержки фото в polling-режиме, можно добавить позже
            image_data = None

            try:
                result = ChannelHandler.process_incoming_message(
                    channel=Channel.CHANNEL_TELEGRAM,
                    user_identifier=str(user_id),
                    text=text,
                    image_data=image_data,
                    external_id=str(chat_id),
                    metadata={
                        "username": username,
                        "full_name": full_name,
                        "chat_id": chat_id,
                    },
                )
                reply = result.get("reply") or "Извините, произошла ошибка при обработке запроса."
                send_message(chat_id, reply)
            except Exception as e:
                print(f"[ERROR] Ошибка обработки сообщения: {e}")
                send_message(chat_id, "Извините, возникла техническая ошибка. Попробуйте позже.")

        # Небольшая пауза, чтобы не крутить цикл слишком часто
        time.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[INFO] Остановка polling скрипта.")
