import os
import time
from playwright.sync_api import sync_playwright

# Точная часть названия чата из твоего списка
TARGET_CHAT_NAME = "Чат игроков rahatov" 
MESSAGE_TEXT = "1337"

def remove_onboarding_overlays(page):
    """Надежно закрывает модальное окно кликом на крестик или удаляет его из DOM"""
    try:
        close_btn = page.locator("svg.icon-close, button.close-button, div.modal button, [class*='close']").last
        if close_btn.is_visible(timeout=3000):
            close_btn.click()
            print("✔ Кликнули по крестику закрытия модалки.")
            time.sleep(1)
    except Exception:
        pass

    page.evaluate("""() => {
        const unwantedSelectors = [
            '.popup', '.modal', '.auth-modal', '.welcome', '.settings', 
            '.tooltip', '.tip', '.popover',
            '[class*="popup"]', '[class*="modal"]', '[class*="welcome"]',
            '[class*="onboarding"]', '[class*="intro"]', '[class*="backdrop"]',
            '[class*="overlay"]'
        ];
        
        unwantedSelectors.forEach(sel => {
            document.querySelectorAll(sel).forEach(el => {
                if (el.id !== 'column-left' && el.id !== 'column-center' && el.id !== 'column-right') {
                    el.remove();
                }
            });
        });

        const allDivs = document.querySelectorAll('div');
        allDivs.forEach(el => {
            const text = el.innerText || '';
            if ((text.includes('Appearance') || text.includes('Color theme') || text.includes('Next Tip')) && 
                el.childElementCount < 15 && !el.id.includes('column')) {
                el.remove();
            }
        });

        if (document.body) {
            document.body.style.overflow = 'auto';
            document.body.classList.remove('modal-open');
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
            time.sleep(4)

            print("Закрываем окно настройки...")
            remove_onboarding_overlays(page)
            time.sleep(2)

            print(f"2. Ищем чат '{TARGET_CHAT_NAME}' в списке слева...")
            # Ищем элемент списка чатов, содержащий нужное название, и кликаем по нему
            chat_item = page.locator(f"#column-left div.chat-item:has-text('{TARGET_CHAT_NAME}')").first
            chat_item.wait_for(state="visible", timeout=15000)
            chat_item.click()
            time.sleep(2)

            print("3. Ищем поле ввода сообщения...")
            input_box = page.locator("div.input-message-input[contenteditable='true'], div[contenteditable='true']").first
            input_box.wait_for(state="visible", timeout=25000)
            
            input_box.click()
            time.sleep(1)
            input_box.fill(MESSAGE_TEXT)
            time.sleep(1)
            page.keyboard.press("Enter")
            
            print(f"✔ Сообщение '{MESSAGE_TEXT}' успешно отправлено в чат!")
            time.sleep(3)
            
        except Exception as e:
            print(f"✖ Ошибка при отправке: {e}")
            page.screenshot(path="error.png")
            print("📸 Скриншот ошибки сохранен в error.png")
        finally:
            browser.close()

if __name__ == "__main__":
    send_message()
