import os
import requests
from playwright.sync_api import sync_playwright

def notify(text):
    token = os.environ["TG_TOKEN"]
    chat_id = os.environ["TG_CHAT_ID"]
    requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data={"chat_id": chat_id, "text": text}
    )

def safe_screenshot(page, name):
    try:
        page.screenshot(path=name, full_page=True)
    except Exception as e:
        print(f"Не удалось сделать скриншот {name}: {e}")

def dismiss_cookie_banner(page):
    for text in ["Elfogadom", "Accept", "OK", "Rendben", "Egyetértek"]:
        try:
            btn = page.get_by_text(text, exact=False)
            if btn.count() > 0:
                btn.first.click(timeout=3000)
                print(f"Закрыт баннер с текстом: {text}")
                page.wait_for_timeout(1000)
        except Exception:
            pass

def select_location_and_service(page):
    page.get_by_text("Helyszín kiválasztása").click(timeout=10000)
    page.wait_for_timeout(500)
    page.get_by_text("Szerbia - Szabadka, Főkonzulátus").click(timeout=10000)
    page.wait_for_timeout(500)

    page.get_by_text("Ügytípus hozzáadása").click(timeout=10000)
    page.wait_for_timeout(500)
    page.get_by_text("Vízumkérelem (schengeni - C)").click(timeout=10000)
    page.wait_for_timeout(500)

def fill_form(page):
    page.get_by_label("Kérelmezők száma").fill(os.environ.get("VISA_APPLICANTS_COUNT", "1"))
    page.get_by_label("Név").fill(os.environ["VISA_NAME"])
    page.get_by_label("Születési idő").fill(os.environ["VISA_BIRTHDATE"])
    page.get_by_label("Értesítési telefonszám").fill(os.environ["VISA_PHONE"])
    page.get_by_label("E-mail cím").fill(os.environ["VISA_EMAIL"])
    page.get_by_label("E-mail cím újra").fill(os.environ["VISA_EMAIL"])

    if os.environ.get("VISA_RESIDENCE_PERMIT"):
        page.get_by_label("Szerb tartózkodási engedély száma, érvényessége").fill(os.environ["VISA_RESIDENCE_PERMIT"])

    page.get_by_label("Állampolgárság").fill(os.environ["VISA_NATIONALITY"])
    page.get_by_label("Útlevél száma").fill(os.environ["VISA_PASSPORT"])

    if os.environ.get("VISA_RESIDENCE_COMMUNITY"):
        page.get_by_label("Residential community in Serbia").fill(os.environ["VISA_RESIDENCE_COMMUNITY"])

    checkboxes = page.locator("input[type=checkbox]")
    for i in range(checkboxes.count()):
        checkboxes.nth(i).check()

def check_calendar_for_slots(page):
    content = page.content()
    no_slots_markers = ["ninc
