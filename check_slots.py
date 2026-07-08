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
    labels = ["Elfogadom", "Accept", "OK", "Rendben", "Egyetertek"]
    for text in labels:
        try:
            btn = page.get_by_text(text, exact=False)
            if btn.count() > 0:
                btn.first.click(timeout=3000)
                print("Закрыт баннер: " + text)
                page.wait_for_timeout(1000)
        except Exception:
            pass

def select_location_and_service(page):
    page.get_by_text("Helyszin kivalasztasa").click(timeout=10000)
    page.wait_for_timeout(500)
    page.get_by_text("Szerbia").click(timeout=10000)
    page.wait_for_timeout(500)
    page.get_by_text("Ugytipus hozzaadasa").click(timeout=10000)
    page.wait_for_timeout(500)
    page.get_by_text("Vizumkerelem").click(timeout=10000)
    page.wait_for_timeout(500)

def fill_form(page):
    page.get_by_label("Kerelmezok szama").fill(os.environ.get("VISA_APPLICANTS_COUNT", "1"))
    page.get_by_label("Nev").fill(os.environ["VISA_NAME"])
    page.get_by_label("Szuletesi ido").fill(os.environ["VISA_BIRTHDATE"])
    page.get_by_label("Ertesitesi telefonszam").fill(os.environ["VISA_PHONE"])
    page.get_by_label("E-mail cim").fill(os.environ["VISA_EMAIL"])

    checkboxes = page.locator("input[type=checkbox]")
    for i in range(checkboxes.count()):
        checkboxes.nth(i).check()

def check_calendar_for_slots(page):
    content = page.content()
    markers = ["nincs szabad", "nincs elerheto", "no available"]
    has_slots = True
    for m in markers:
        if m in content.lower():
            has_slots = False
    return has_slots

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto("https://konzinfoidopont.mfa.gov.hu/", timeout=60000)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)
        safe_screenshot(page, "step
