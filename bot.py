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

# ПРЯМАЯ ССЫЛКА НА ТВОЙ ЧАТ
TARGET_LINK = "https://web.telegram.org/a/#-1002455061728" 

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
        print("Запуск браузера Chromium...")
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox"
            ]
        )
        context = browser.new_context(
            storage_state=auth_path,
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            print("1. Открываем прямую ссылку на чат...")
            page.goto(TARGET_LINK, timeout=60000)
            
            print("2. Ожидаем 30 секунд для прогрузки чата...")
            time.sleep(30)

            print("3. Удаляем оверлеи (если есть)...")
            remove_onboarding_overlays(page)
            time.sleep(2)

            print("4. Ищем поле ввода сообщения в чате...")
            # Пробуем универсальные селекторы для поля ввода в Telegram Web A
            input_box = page.locator("div.input-message-input[contenteditable='true'], div[contenteditable='true'], .composer-input input, div.editable-input").first
            
            print("Ожидаем видимости поля ввода (таймаут 20 сек)...")
            input_box.wait_for(state="visible", timeout=20000)
            print("✔ Поле ввода найдено!")
            
            input_box.click()
            time.sleep(1)
            
            print("5. Вставляем текст через JavaScript...")
            page.evaluate(f"""(text) => {{
                const box = document.querySelector("div.input-message-input[contenteditable='true'], div[contenteditable='true'], .composer-input input, div.editable-input");
                if (box) {{
                    box.focus();
                    box.innerText = text;
                    box.dispatchEvent(new Event('input', {{ bubbles: true }}));
                }}
            }}""", MESSAGE_TEXT)
            
            time.sleep(1.5)
            print("6. Нажимаем Enter для отправки...")
            page.keyboard.press("Enter")
            print("✔ Сообщение успешно отправлено в чат по прямой ссылке!")
            time.sleep(3)
            
        except Exception as e:
            print(f"✖ Ошибка выполнения на конкретном шаге: {e}")
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
