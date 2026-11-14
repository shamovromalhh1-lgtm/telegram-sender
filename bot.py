import os
import time
from playwright.sync_api import sync_playwright

# Вставьте сюда точную ссылку на ваш чат из версии /k/
TARGET_CHAT_URL = "https://web.telegram.org/k/#-2455061728"
MESSAGE_TEXT = "Привет!."

def dismiss_onboarding(page):
    """Прокликивает или закрывает приветственные окна настройки (тема, эмодзи)"""
    for _ in range(4):
        try:
            # Ищем любую кнопку подтверждения в модальном окне (Next, Continue, Skip, Done, Продолжить, Далее)
            btn = page.locator(".popup button.btn-primary, .popup-peer button, button:has-text('Next'), button:has-text('Continue'), button:has-text('Skip'), button:has-text('Продолжить'), button:has-text('Далее')").first
            if btn.is_visible(timeout=2000):
                print("Закрываем экран настройки...")
                btn.click()
                time.sleep(1.5)
            else:
                break
        except Exception:
            break

    # На случай если поверх интерфейса всё равно остался слой-заглушка (popup), убираем его принудительно
    page.evaluate("""
        document.querySelectorAll('.popup, .popup-container').forEach(el => el.remove());
    """)

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
            print("1. Загружаем Telegram Web...")
            page.goto("https://web.telegram.org/k/", timeout=60000)
            
            # Ждем загрузки интерфейса
            page.wait_for_selector("#column-left", timeout=30000)
            time.sleep(3)

            # Проходим/убираем окно с выбором темы и эмодзи
            dismiss_onboarding(page)

            print(f"2. Переходим по прямой ссылке в чат: {TARGET_CHAT_URL}")
            page.goto(TARGET_CHAT_URL, timeout=60000)
            time.sleep(3)
            
            # На случай если окно вылезло повторно после перехода
            dismiss_onboarding(page)

            print("3. Ищем поле ввода сообщения...")
            input_box = page.locator("div.input-message-input[contenteditable='true']").first
            input_box.wait_for(state="visible", timeout=25000)
            
            input_box.click()
            time.sleep(1)
            input_box.fill(MESSAGE_TEXT)
            time.sleep(1)
            page.keyboard.press("Enter")
            
            print("✔ Сообщение успешно отправлено в нужный чат!")
            time.sleep(3)
            
        except Exception as e:
            print(f"✖ Ошибка при отправке: {e}")
            page.screenshot(path="error.png")
            print("📸 Скриншот ошибки сохранен в error.png")
        finally:
            browser.close()

if __name__ == "__main__":
    send_message()
