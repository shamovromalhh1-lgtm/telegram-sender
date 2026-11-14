import os
import time
from playwright.sync_api import sync_playwright

TARGET_CHAT_URL = "https://web.telegram.org/k/#-2455061728"
MESSAGE_TEXT = "Привет! Сообщение отправлено с личного аккаунта."

def close_settings_screen(page):
    """Находит реальную кнопку закрытия/назад (не лампочку!) и закрывает экран настройки"""
    closed = page.evaluate("""() => {
        // Ищем все кнопки в шапке экрана (кроме лампочки lamp_filled)
        const btns = Array.from(document.querySelectorAll('button.btn-icon'));
        for (const btn of btns) {
            const cls = btn.className || '';
            const txt = btn.textContent || '';
            // Ищем иконку крестика или стрелки назад
            if (cls.includes('close') || cls.includes('back') || cls.includes('arrow') || txt.includes('close') || txt.includes('arrow_left')) {
                ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click'].forEach(type => {
                    btn.dispatchEvent(new MouseEvent(type, { bubbles: true, cancelable: true, view: window }));
                });
                return 'Нажата кнопка: ' + cls;
            }
        }
        return 'Кнопка закрытия не найдена';
    }""")
    print(closed)

    # Дополнительно проверяем: если правая колонка или слайдер настройки перекрывает чаты — скрываем его
    page.evaluate("""() => {
        // Если открыт слайдер в левой или правой колонке, возвращаем фокус на список чатов
        const leftTabs = document.querySelector('#column-left .tabs-container');
        if (leftTabs && leftTabs.children.length > 1) {
            // Удаляем все дополнительные вкладки/экраны настройки поверх основного списка чатов
            while (leftTabs.children.length > 1) {
                leftTabs.lastElementChild.remove();
            }
        }
        // Скрываем правую колонку, если в ней открыты настройки
        const rightCol = document.querySelector('#column-right');
        if (rightCol && rightCol.classList.contains('is-active')) {
            rightCol.classList.remove('is-active');
        }
    }""")

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

            close_settings_screen(page)
            time.sleep(2)

            print(f"2. Переходим по прямой ссылке в чат: {TARGET_CHAT_URL}")
            page.goto(TARGET_CHAT_URL, timeout=60000)
            time.sleep(5)

            close_settings_screen(page)
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
