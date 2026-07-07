import os
import time
import requests
from playwright.sync_api import sync_playwright

def notify(text):
    token = os.environ["TG_TOKEN"]
    chat_id = os.environ["TG_CHAT_ID"]
    requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data={"chat_id": chat_id, "text": text}
    )

def check_slots():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://konzinfoidopont.mfa.gov.hu/", timeout=60000)
        page.wait_for_load_state("networkidle")

        content = page.content()
        no_slots_text = "нет свободных"
        has_slots = no_slots_text.lower() not in content.lower()

        browser.close()
        return has_slots

if __name__ == "__main__":
    try:
        if check_slots():
            notify("Похоже, появился свободный слот! Проверьте сайт: https://konzinfoidopont.mfa.gov.hu/")
        else:
            print("Слотов пока нет.")
    except Exception as e:
        print(f"Ошибка при проверке: {e}")
