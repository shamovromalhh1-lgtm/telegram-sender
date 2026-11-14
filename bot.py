import os
import time
from playwright.sync_api import sync_playwright

# ОБЯЗАТЕЛЬНО: вставьте сюда точную ссылку на чат из адресной строки браузера
# Пример: "https://web.telegram.org/k/#@durov" или "https://web.telegram.org/k/#-1001234567890"
TARGET_CHAT_URL = "https://web.telegram.org/k/#-1002455061728"
MESSAGE_TEXT = "Привет."

def send_message():
    auth_data = os.environ.get("TELEGRAM_AUTH_JSON")
    if not auth_data:
        print("✖ Ошибка: не найден секрет TELEGRAM_AUTH_JSON")
        return

    with open("auth.json", "w", encoding="utf-8") as f:
        f.write(auth_data)

    with sync_playwright() as p:
        # Добавляем маскировку под обычный браузер
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(
            storage_state="auth.json",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            print(f"Переходим по адресу: {TARGET_CHAT_URL}")
            page.goto(TARGET_CHAT_URL, timeout=60000)
            
            # Ждем загрузки интерфейса (увеличили время до 45 сек)
            input_box = page.wait_for_selector(".input-message-input", timeout=45000)
            time.sleep(2)
            
            input_box.click()
            input_box.fill(MESSAGE_TEXT)
            time.sleep(1)
            page.keyboard.press("Enter")
            
            print("✔ Сообщение успешно отправлено с вашего аккаунта!")
            time.sleep(3)
        except Exception as e:
            print(f"✖ Ошибка при отправке: {e}")
            # Делаем скриншот экрана, чтобы увидеть, что открылось в браузере
            page.screenshot(path="error.png")
            print("📸 Скриншот ошибки сохранен в error.png")
        finally:
            browser.close()

if __name__ == "__main__":
    send_message()
