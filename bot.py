import os
import time
from playwright.sync_api import sync_playwright

TARGET_CHAT_URL = "https://web.telegram.org/k/#-2455061728"
MESSAGE_TEXT = "Привет! Сообщение отправлено с личного аккаунта."

CLOSE_X = 1245
CLOSE_Y = 35

def force_close_at_coords(page, x, y):
    """Находит родительскую кнопку под ripple-слоем и эмулирует реальное нажатие мыши"""
    clicked_tag = page.evaluate(f"""() => {{
        const el = document.elementFromPoint({x}, {y});
        if (!el) return 'none';
        const btn = el.closest('button, .btn-icon, [role="button"]') || el;
        ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click'].forEach(type => {{
            btn.dispatchEvent(new MouseEvent(type, {{
                bubbles: true,
                cancelable: true,
                view: window,
                clientX: {x},
                clientY: {y}
            }}));
        }});
        return btn.tagName + '.' + (btn.className || '');
    }}""")
    print(f"Нажата кнопка в ({x}, {y}) -> {clicked_tag}")
    page.mouse.move(x, y)
    page.mouse.down()
    time.sleep(0.1)
    page.mouse.up()

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
            page.wait_for_selector("#column-left", timeout=30000)
            time.sleep(5)

            force_close_at_coords(page, CLOSE_X, CLOSE_Y)
            time.sleep(2)

            print(f"2. Переходим по прямой ссылке в чат: {TARGET_CHAT_URL}")
            page.goto(TARGET_CHAT_URL, timeout=60000)
            time.sleep(5)

            force_close_at_coords(page, CLOSE_X, CLOSE_Y)
            time.sleep(2)

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
