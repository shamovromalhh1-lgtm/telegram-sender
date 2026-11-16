import os
import time
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

# --- СПИСОК ЧАТОВ И СООБЩЕНИЙ ---
TASKS = [
    {
        "link": "https://web.telegram.org/a/#-1003130768925_9",
        "text": """Продам:
Цешка на виниле - 4ккк
G90 на виниле - 3 ккк"""
    },
    {
        "link": "https://web.telegram.org/a/#-1003130768925_7",
        "text": """Куплю:

Донат авто - любой стоимости

Так же беру имущество под выкуп, что бы вам отыграться, процент минимальный"""
    },
    {
        "link": "https://web.telegram.org/a/#-1003130768925_11",
        "text": """Продам:
Номера
К001УМ01 - 250кк
Т001ЕР01 - 250кк
К001МС01 - 250кк
Р001ОМ77 - 50кк"""
    },
    {
        "link": "https://web.telegram.org/a/#-1002455061728",
        "text": """Куплю:

Донат авто - любой стоимости

Так же беру имущество под выкуп, что бы вам отыграться, процент минимальный

Продам:
Номера
К001УМ01 - 250кк
Т001ЕР01 - 250кк
К001МС01 - 250кк
Р001ОМ77 - 50кк
Машины
Цешка на виниле - 4ккк
G90 на виниле - 3 ккк"""
    }
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

def run_mailing_cycle():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    auth_path = os.path.join(base_dir, "auth.json")

    # Если запуск идет на GitHub Actions, создаем auth.json из секретов
    auth_env = os.environ.get("AUTH_JSON_SECRET")
    if auth_env:
        with open(auth_path, "w", encoding="utf-8") as f:
            f.write(auth_env)

    if not os.path.exists(auth_path):
        print(f"✖ Ошибка: файл auth.json не найден по пути: {auth_path}")
        return

    with sync_playwright() as p:
        print("Запуск браузера...")
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
            for index, task in enumerate(TASKS, 1):
                target_link = task["link"]
                message_text = task["text"]
                
                print(f"\n--- Отправка сообщения {index} из {len(TASKS)} ---")
                print(f"Переходим в чат: {target_link}")
                
                # 1. Полностью очищаем страницу (переходим на пустой адрес или корень), 
                # чтобы сбросить предыдущий кэш чата в Telegram Web
                page.goto("about:blank", timeout=30000)
                time.sleep(1)

                # 2. Переходим по целевой ссылке
                page.goto(target_link, timeout=60000)
                
                # Даем время на прогрузку интерфейса раздела
                time.sleep(7)
                
                remove_onboarding_overlays(page)

                print("Ищем поле ввода сообщения...")
                input_box = page.locator("div[contenteditable='true']").last
                input_box.wait_for(state="visible", timeout=20000)
                
                input_box.click()
                time.sleep(1)
                
                # Очищаем поле ввода на всякий случай
                page.keyboard.press("Control+A")
                page.keyboard.press("Backspace")
                time.sleep(0.5)

                clean_text = message_text.replace("**", "")
                
                # Вставляем текст через JS
                page.evaluate(f"""(text) => {{
                    const boxes = document.querySelectorAll("div[contenteditable='true']");
                    const box = boxes[boxes.length - 1];
                    if (box) {{
                        box.focus();
                        box.innerText = text;
                        box.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    }}
                }}""", clean_text)
                
                time.sleep(1)
                
                # Выделяем, делаем жирным и отправляем
                page.keyboard.press("Control+A")
                time.sleep(0.5)
                page.keyboard.press("Control+B")
                time.sleep(1)
                
                page.keyboard.press("Enter")
                print(f"✔ Сообщение {index} успешно отправлено!")
                
                # Пауза 12 секунд между разделами, чтобы избежать Slow Mode
                print("⏳ Пауза 12 секунд перед следующим разделом...")
                time.sleep(12)

        except Exception as e:
            print(f"✖ Ошибка во время рассылки: {e}")
            page.screenshot(path="error.png")
        finally:
            browser.close()

def wait_until_next_hour():
    now = datetime.now()
    next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    sleep_seconds = (next_hour - now).total_seconds()
    
    print(f"\n⏳ Все задачи выполнены. Следующая рассылка в ровно {next_hour.strftime('%H:%M:%S')}")
    time.sleep(sleep_seconds)

if __name__ == "__main__":
    print("=== Мульти-чат бот запущен ===")
    
    while True:
        print(f"\n=== Начало цикла рассылки: {datetime.now().strftime('%H:%M:%S')} ===")
        run_mailing_cycle()
        wait_until_next_hour()
