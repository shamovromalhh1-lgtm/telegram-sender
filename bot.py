import os
import time
import threading
from flask import Flask
from playwright.sync_api import sync_playwright

# --- МИНИ-СЕРВЕР ДЛЯ RENDER (ДОЛЖЕН СТАРТОВАТЬ ПЕРВЫМ) ---
app = Flask(__name__)

@app.route("/")
def home():
    return "Telegram Bot is running!", 200

# ТВОЙ ТЕКСТ С ЖИРНЫМ ШРИФТОМ
MESSAGE_TEXT = """**Куплю:**

**Донат 1 рубль = 700к**
**Пополнение через логин на сайте, с договором и откатом**

**Донат авто - любой стоимости**

**Так же беру имущество под выкуп, что бы вам отыграться, процент минимальный**"""

# СПИСОК ЧАТОВ (точное название)
TARGET_CHATS = [
    "Чат игроков rahatov.mta",       
]

def remove_onboarding_overlays(page):
    try:
        close_btn = page.locator("svg.icon-close, button.close-button, div.modal button, [class*='close']").last
        if close_btn.is_visible(timeout=3000):
            close_btn.click()
            time.sleep(1)
    except Exception:
        pass

    page.evaluate("""() => {
        const unwantedSelectors = ['.popup', '.modal', '.welcome', '.settings', '.overlay'];
        unwantedSelectors.forEach(sel => {
            document.querySelectorAll(sel).forEach(el => {
                if (el.id !== 'column-left' && el.id !== 'column-center' && el.id !== 'column-right') {
                    el.remove();
                }
            });
        });
        if (document.body) {
            document.body.style.overflow = 'auto';
            document.body.classList.remove('modal-open');
        }
    }""")

def send_message():
    auth_path = "/etc/secrets/auth.json"
    if not os.path.exists(auth_path):
        auth_path = "auth.json"

    if not os.path.exists(auth_path):
        print(f"✖ Ошибка: файл авторизации не найден ни по пути {auth_path}, ни локально!")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(
            storage_state=auth_path,
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            print("1. Загружаем Telegram Web...")
            page.goto("https://web.telegram.org/k/", timeout=60000)
            
            print("2. Ожидаем прогрузку интерфейса...")
            page.wait_for_selector("#column-left", timeout=40000)
            time.sleep(6)

            remove_onboarding_overlays(page)
            time.sleep(2)

            for chat_name in TARGET_CHATS:
                print(f"\n--- Ищем и переходим к чату: '{chat_name}' ---")
                
                if page.url != "https://web.telegram.org/k/":
                    page.goto("https://web.telegram.org/k/", timeout=30000)
                    time.sleep(3)
                    remove_onboarding_overlays(page)

                # Сначала ищем в видимой левой панели
                chat_item = page.locator("#column-left").get_by_text(chat_name).first
                
                try:
                    chat_item.wait_for(state="visible", timeout=5000)
                    chat_item.click()
                except Exception:
                    print("Чат не найден на первом экране, используем поиск Telegram...")
                    search_box = page.locator("input#input-search").first
                    search_box.wait_for(state="visible", timeout=10000)
                    search_box.click()
                    search_box.fill(chat_name)
                    time.sleep(2)
                    
                    result_item = page.locator(".search-super-results .chat-item, .found-peers .chat-item, #column-left .chat-item").first
                    result_item.wait_for(state="visible", timeout=10000)
                    result_item.click()

                time.sleep(2)

                print("3. Вводим текст через JS и отправляем...")
                input_box = page.locator("div.input-message-input[contenteditable='true'], div[contenteditable='true']").first
                input_box.wait_for(state="visible", timeout=25000)
                
                input_box.click()
                time.sleep(1)
                
                page.evaluate(f"""(text) => {{
                    const box = document.querySelector("div.input-message-input[contenteditable='true'], div[contenteditable='true']");
                    if (box) {{
                        box.focus();
                        box.innerText = text;
                        box.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    }}
                }}""", MESSAGE_TEXT)
                
                time.sleep(1.5)
                page.keyboard.press("Enter")
                print(f"✔ Сообщение успешно отправлено в чат: {chat_name}!")
                time.sleep(2)
            
            print("\n✔ Все сообщения по всем чатам успешно отправлены!")
            time.sleep(3)
            
        except Exception as e:
            print(f"✖ Ошибка: {e}")
            page.screenshot(path="error.png")
        finally:
            browser.close()

def bot_loop():
    time.sleep(5)
    while True:
        print("\n=== Запуск цикла отправки сообщений ===")
        send_message()
        print("⏳ Ожидание 5 минут до следующей отправки...")
        time.sleep(300)

if __name__ == "__main__":
    bot_thread = threading.Thread(target=bot_loop)
    bot_thread.daemon = True
    bot_thread.start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
