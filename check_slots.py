import os
import requests
from playwright.sync_api import sync_playwright

INTERVAL_MINUTES = 15  # задаётся в workflow через cron, тут просто справочно

def notify(text):
    token = os.environ["TG_TOKEN"]
    chat_id = os.environ["TG_CHAT_ID"]
    requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data={"chat_id": chat_id, "text": text}
    )

def fill_form(page):
    page.get_by_label("Фамилия, имя (латинскими буквами)").fill(os.environ["VISA_NAME"])
    page.get_by_label("Дата рождения").fill(os.environ["VISA_BIRTHDATE"])
    page.get_by_label("Номер телефона для уведомления").fill(os.environ["VISA_PHONE"])
    page.get_by_label("Адрес эл.почты").fill(os.environ["VISA_EMAIL"])
    page.get_by_label("Повторить адрес электронной почты").fill(os.environ["VISA_EMAIL"])

    # Необязательные поля — заполняем, только если переменная задана
    if os.environ.get("VISA_RESIDENCE_PERMIT"):
        page.get_by_label("Serbian residence permit number and validity").fill(os.environ["VISA_RESIDENCE_PERMIT"])
    if os.environ.get("VISA_RESIDENCE_COMMUNITY"):
        page.get_by_label("Residential community in Serbia").fill(os.environ["VISA_RESIDENCE_COMMUNITY"])

    page.get_by_label("Гражданство").fill(os.environ["VISA_NATIONALITY"])
    page.get_by_label("Номер паспорта").fill(os.environ["VISA_PASSPORT"])

    # Отметить оба чекбокса согласия
    checkboxes = page.locator("input[type=checkbox]")
    for i in range(checkboxes.count()):
        checkboxes.nth(i).check()

def select_location_and_service(page):
    # TODO: уточнить после первого прогона — как выглядит выпадающий список
    #판단: вероятно это Blazor select или кастомный dropdown (не <select>)
    # Пример для обычного select:
    # page.select_option("select#location", label="Сербия - Субботица, Генеральное консульство")
    # page.select_option("select#service", label="Visa application (Schengen visa- type 'C')")

    # Если это кастомные dropdown-кнопки (судя по тёмно-синим полосам "Выбор места" на скринах):
    page.get_by_text("Выбор места").click()
    page.get_by_text("Сербия - Субботица, Генеральное консульство").click()

    page.get_by_text("Добавление типа услуги").click()
    page.get_by_text("Visa application (Schengen visa- type 'C')").click()

def check_calendar_for_slots(page):
    # TODO: уточнить реальный маркер "нет мест" после скриншота календаря
    content = page.content()
    no_slots_markers = ["нет свободных", "нет доступных", "no available"]
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

        # Нажать "Далее" — TODO: уточнить точный текст кнопки
        page.get_by_role("button", name="Далее").click()
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
