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

def select_location_and_service(page):
    page.get_by_text("Helyszín kiválasztása").click()
    page.get_by_text("Szerbia - Szabadka, Főkonzulátus").click()

    page.get_by_text("Ügytípus hozzáadása").click()
    page.get_by_text("Vízumkérelem (schengeni - C)").click()

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
    no_slots_markers = ["nincs szabad", "nincs elérhető", "no available"]
    has_slots = not any(marker in content.lower() for marker in no_slots_markers)
    return has_slots

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto("https://konzinfoidopont.mfa.gov.hu/", timeout=60000)
        page.wait_for_load_state("networkidle")
        page.screenshot(path="step1_initial.png", full_page=True)

        select_location_and_service(page)
        page.screenshot(path="step2_after_selection.png", full_page=True)

        fill_form(page)
        page.screenshot(path="step3_after_fill.png", full_page=True)

        page.get_by_role("button", name="Tovább az időpontválasztáshoz »").click()
        page.wait_for_load_state("networkidle")
        page.screenshot(path="step4_calendar.png", full_page=True)

        has_slots = check_calendar_for_slots(page)

        browser.close()
        return has_slots

if __name__ == "__main__":
    try:
        result = run()
        if result:
            notify("🎉 Похоже, появился свободный слот! Проверьте сайт: https://konzinfoidopont.mfa.gov.hu/")
        else:
            print("Слотов пока нет.")
    except Exception as e:
        print(f"Ошибка: {e}")
        notify(f"⚠️ Бот столкнулся с ошибкой при проверке: {e}")
