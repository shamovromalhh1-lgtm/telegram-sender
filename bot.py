import os
import time
from playwright.sync_api import sync_playwright

# Вставьте сюда точную ссылку на чат (например: "https://web.telegram.org/k/#-1001234567890" или "https://web.telegram.org/k/#@username")
TARGET_CHAT_URL = "https://web.telegram.org/k/#-1414337259"
MESSAGE_TEXT = "Привет! Сообщение отправлено с личного аккаунта."

def send_message():
    auth_data = os.environ.get("TELEGRAM_AUTH_JSON")
    if not auth_data:
        print("✖ Ошибка: не найден секрет TELEGRAM_AUTH_JSON")
        return

    with open("auth.json", "w", encoding="utf-8") as f:
        f.write(auth_data)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(
            storage_state="auth.json",
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            print("1. Открываем главную страницу Telegram Web...")
            page.goto("https://web.telegram.org/k/", timeout=60000)
            time.sleep(5) # Даем время прогрузиться сессии и чатам

            print(f"2. Переходим в целевой чат: {TARGET_CHAT_URL}")
            page.goto(TARGET_CHAT_URL, timeout=60000)
            time.sleep(4)

            # Ищем поле ввода по любому из возможных признаков в Telegram Web K
            print("3. Ищем поле для ввода сообщения...")
            input_box = page.locator("div.input-message-input[contenteditable='true'], div[data-peer-id] div[contenteditable='true']").first
            input_box.wait_for(state="visible", timeout=30000)
            
            input_box.click()
            time.sleep(1)
            input_box.fill(MESSAGE_TEXT)
            time.sleep(1)
            page.keyboard.press("Enter")
            
            print("✔ Сообщение успешно отправлено с вашего аккаунта!")
            time.sleep(3)
            
        except Exception as e:
            print(f"✖ Ошибка при отправке: {e}")
            page.screenshot(path="error.png")
            print("📸 Скриншот экрана сохранен в error.png")
        finally:
            browser.close()

if __name__ == "__main__":
    send_message()
