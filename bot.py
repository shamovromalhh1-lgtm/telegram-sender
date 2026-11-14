import os
import time
from playwright.sync_api import sync_playwright

# Впишите точное название чата или его @username, как оно отображается в поиске Telegram
CHAT_NAME = "Чат игроков rahatov.mta"
MESSAGE_TEXT = "Привет."

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
            print("1. Открываем Telegram Web...")
            page.goto("https://web.telegram.org/k/", timeout=60000)

            # Ждем загрузки строки поиска (значит, авторизация прошла успешно)
            search_input = page.locator("input.input-search-input").first
            search_input.wait_for(state="visible", timeout=30000)
            print("✔ Вход в аккаунт выполнен!")

            # Вводим название чата в поиск
            print(f"2. Ищем чат: {CHAT_NAME}")
            search_input.click()
            search_input.fill(CHAT_NAME)
            time.sleep(3)

            # Кликаем по первому найденному результату в списке поиска
            first_result = page.locator(".search-group .chatlist-chat, .chatlist-chat").first
            first_result.wait_for(state="visible", timeout=15000)
            first_result.click()
            time.sleep(2)

            # Находим поле ввода и отправляем сообщение
            print("3. Отправляем сообщение...")
            input_box = page.locator("div.input-message-input[contenteditable='true']").first
            input_box.wait_for(state="visible", timeout=15000)
            input_box.click()
            input_box.fill(MESSAGE_TEXT)
            time.sleep(1)
            page.keyboard.press("Enter")

            print("✔ Сообщение успешно отправлено!")
            time.sleep(3)

        except Exception as e:
            print(f"✖ Ошибка: {e}")
            page.screenshot(path="error.png")
        finally:
            browser.close()

if __name__ == "__main__":
    send_message()
