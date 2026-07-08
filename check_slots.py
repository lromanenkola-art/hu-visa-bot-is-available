cat > /home/claude/check_slots.py << 'PYEOF'
import os
import requests
from playwright.sync_api import sync_playwright

def notify(text):
    token = os.environ["TG_TOKEN"]
    chat_id = os.environ["TG_CHAT_ID"]
    requests.post(
        "https://api.telegram.org/bot" + token + "/sendMessage",
        data={"chat_id": chat_id, "text": text}
    )

def safe_screenshot(page, name):
    try:
        page.screenshot(path=name, full_page=True)
    except Exception as e:
        print("Не удалось сделать скриншот " + name + ": " + str(e))

def dismiss_cookie_banner(page):
    labels = ["Elfogadom", "Accept", "OK", "Rendben"]
    for text in labels:
        try:
            btn = page.get_by_text(text, exact=False)
            if btn.count() > 0:
                btn.first.click(timeout=3000)
                page.wait_for_timeout(1000)
        except Exception:
            pass

def select_location_and_service(page):
    page.locator("text=Helyszín kiválasztása").click(timeout=10000)
    page.wait_for_timeout(500)
    page.locator("text=Szerbia").first.click(timeout=10000)
    page.wait_for_timeout(500)
    page.locator("text=Ügytípus hozzáadása").click(timeout=10000)
    page.wait_for_timeout(500)
    page.locator("text=Vízumkérelem").first.click(timeout=10000)
    page.wait_for_timeout(500)

def fill_form(page):
    inputs = page.locator("input:not([type=checkbox])")
    count = inputs.count()
    print("Найдено полей ввода: " + str(count))

    values = [
        os.environ.get("VISA_NAME", ""),
        os.environ.get("VISA_BIRTHDATE", ""),
        os.environ.get("VISA_APPLICANTS_COUNT", "1"),
        os.environ.get("VISA_PHONE", ""),
        os.environ.get("VISA_EMAIL", ""),
        os.environ.get("VISA_EMAIL", ""),
        os.environ.get("VISA_RESIDENCE_PERMIT", ""),
        os.environ.get("VISA_NATIONALITY", ""),
        os.environ.get("VISA_PASSPORT", ""),
        os.environ.get("VISA_RESIDENCE_COMMUNITY", "")
    ]

    for i in range(len(values)):
        if i >= count:
            break
        val = values[i]
        if val:
            try:
                inputs.nth(i).fill(val)
            except Exception as e:
                print("Не удалось заполнить поле номер " + str(i) + ": " + str(e))

    checkboxes = page.locator("input[type=checkbox]")
    for i in range(checkboxes.count()):
        try:
            checkboxes.nth(i).check()
        except Exception as e:
            print("Не удалось отметить чекбокс номер " + str(i) + ": " + str(e))

def check_calendar_for_slots(page):
    content = page.content().lower()
    markers = ["nincs szabad", "nincs elérhető", "no available"]
    has_slots = True
    for m in markers:
        if m in content:
            has_slots = False
    return has_slots

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto("https://konzinfoidopont.mfa.gov.hu/", timeout=60000)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)
        safe_screenshot(page, "step1_initial.png")

        try:
            dismiss_cookie_banner(page)
            safe_screenshot(page, "step1b_after_cookies.png")
        except Exception as e:
            print("Ошибка на этапе cookies: " + str(e))

        try:
            select_location_and_service(page)
            safe_screenshot(page, "step2_after_selection.png")
        except Exception as e:
            print("Ошибка на этапе выбора места/услуги: " + str(e))
            safe_screenshot(page, "error_step2.png")
            browser.close()
            return None

        try:
            fill_form(page)
            safe_screenshot(page, "step3_after_fill.png")
        except Exception as e:
            print("Ошибка на этапе заполнения формы: " + str(e))
            safe_screenshot(page, "error_step3.png")
            browser.close()
            return None

        try:
            page.locator("text=Tovább").first.click(timeout=10000)
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(1000)
            safe_screenshot(page, "step4_calendar.png")
        except Exception as e:
            print("Ошибка на этапе перехода к календарю: " + str(e))
            safe_screenshot(page, "error_step4.png")
            browser.close()
            return None

        has_slots = check_calendar_for_slots(page)
        browser.close()
        return has_slots

if __name__ == "__main__":
    try:
        result = run()
        if result is True:
            notify("Похоже, появился свободный слот! Проверьте сайт: https://konzinfoidopont.mfa.gov.hu/")
        elif result is False:
            print("Слотов пока нет.")
        else:
            print("Проверка не дошла до конца - смотрите скриншоты error в артефактах.")
    except Exception as e:
        print("Общая ошибка: " + str(e))
PYEOF
python3 -c "
import ast
with open('/home/claude/check_slots.py', encoding='utf-8') as f:
    src = f.read()
ast.parse(src)
print('Синтаксис корректен')
"
