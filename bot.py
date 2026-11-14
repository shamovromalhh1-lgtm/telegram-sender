import os
import json
import time
from playwright.sync_api import sync_playwright

# Ссылка на нужный чат или канал (откройте его в Telegram Web и скопируйте ссылку из адресной строки)
TARGET_CHAT_URL = "https://web.telegram.org/k/#@username_или_id_чата"
MESSAGE_TEXT = "Привет! Сообщение отправлено с личного аккаунта."

def send_message():
    auth_data = os.environ.get("TELEGRAM_AUTH_JSON")
    if not auth_data:
        print("✖ Ошибка: не найден секрет TELEGRAM_AUTH_JSON")
        return

    # Восстанавливаем файл сессии из секрета
    with open("auth.json", "w", encoding="utf-8") as f:
        f.write(auth_data)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Загружаем нашу легкую сессию
        context = browser.new_context(storage_state="auth.json")
        page = context.new_page()

        try:
            page.goto(TARGET_CHAT_URL, timeout=60000)
            # Ждем появления поля ввода сообщения
            input_box = page.wait_for_selector(".input-message-input", timeout=30000)
            time.sleep(2)
            
            input_box.click()
            input_box.fill(MESSAGE_TEXT)
            time.sleep(1)
            page.keyboard.press("Enter")
            
            print("✔ Сообщение успешно отправлено с вашего аккаунта!")
            time.sleep(3) # Даем 3 секунды на отправку перед закрытием браузера
        except Exception as e:
            print(f"✖ Ошибка при отправке: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    send_message()