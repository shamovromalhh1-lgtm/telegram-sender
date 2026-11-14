import os
import time
import threading
from flask import Flask
from playwright.sync_api import sync_playwright

# --- МИНИ-СЕРВЕР ДЛЯ RENDER ---
app = Flask(__name__)

@app.route("/")
def home():
    return "Telegram Bot is running!", 200

MESSAGE_TEXT = """**Куплю:**

**Донат 1 рубль = 700к**
**Пополнение через логин на сайте, с договором и откатом**

**Донат авто - любой стоимости**

**Так же беру имущество под выкуп, что бы вам отыграться, процент минимальный**"""

TARGET_LINK = "https://web.telegram.org/a/#-1002455061728" 

def send_message():
    auth_path = "/etc/secrets/auth.json"
    if not os.path.exists(auth_path):
        auth_path = "auth.json"

    if not os.path.exists(auth_path):
        print(f"✖ Ошибка: файл авторизации не найден ни по пути {auth_path}, ни локально!")
        return

    with sync_playwright() as p:
        print("Запуск браузера Chromium с обходом антибот-защиты...")
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-accelerated-2d-canvas",
                "--no-first-run",
                "--no-zygote",
                "--single-process",
                "--disable-gpu"
            ]
        )
        context = browser.new_context(
            storage_state=auth_path,
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            locale="ru-RU"
        )
        page = context.new_page()

        try:
            print("1. Открываем прямую ссылку на чат...")
            page.goto(TARGET_LINK, timeout=60000)
            
            print("2. Ожидаем 45 секунд для полной прогрузки Telegram Web...")
            time.sleep(45)

            print("3. Проверяем наличие поля ввода сообщения...")
            # Пытаемся найти поле с явным логированием ошибки, если оно не появится
            input_box = page.locator("div[contenteditable='true']").last
            
            print("Ожидаем видимости поля ввода (таймаут 15 сек)...")
            try:
                input_box.wait_for(state="visible", timeout=15000)
                print("✔ Поле ввода успешно найдено!")
            except Exception as wait_err:
                print(f"⚠ Поле ввода не найдено по таймауту! Делаем скриншот state.png... Ошибка: {wait_err}")
                page.screenshot(path="state.png")
                return

            input_box.click()
            time.sleep(1)
            
            print("4. Вставляем текст через JavaScript...")
            page.evaluate(f"""(text) => {{
                const boxes = document.querySelectorAll("div[contenteditable='true']");
                const box = boxes[boxes.length - 1];
                if (box) {{
                    box.focus();
                    box.innerText = text;
                    box.dispatchEvent(new Event('input', {{ bubbles: true }}));
                }}
            }}""", MESSAGE_TEXT)
            
            time.sleep(1.5)
            print("5. Нажимаем Enter для отправки...")
            page.keyboard.press("Enter")
            print("✔ Сообщение успешно отправлено в чат по прямой ссылке!")
            time.sleep(3)
            
        except Exception as e:
            print(f"✖ Общая ошибка выполнения: {e}")
            try:
                page.screenshot(path="error.png")
            except:
                pass
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
