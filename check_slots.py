import os
import requests
from playwright.sync_api import sync_playwright


def notify(text):
    token = os.environ["TG_TOKEN"]
    chat_id = os.environ["TG_CHAT_ID"]

    response = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data={
            "chat_id": chat_id,
            "text": text
        }
    )

    print("Telegram status:", response.status_code)
    print("Telegram response:", response.text)


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
    print("Шаг А: ищу кнопку Helyszin kivalasztasa")
    btn = page.locator("text=Helyszín kiválasztása")
    print("Найдено кнопок 'Helyszín kiválasztása': " + str(btn.count()))
    btn.first.click(timeout=10000)

    print("Шаг Б: жду появления модалки #modal2")
    try:
        page.wait_for_selector("#modal2.show", timeout=8000)
        print("Модалка #modal2 открылась (класс .show найден)")
    except Exception as e:
        print("Модалка #modal2 НЕ открылась через .show: " + str(e))
        modal_count = page.locator("#modal2").count()
        print("Элементов #modal2 в DOM: " + str(modal_count))

    page.wait_for_timeout(500)

    print("Шаг В: ищу label с текстом Szabadka")
    szabadka = page.locator("label:has-text('Szabadka')")
    print("Найдено label с 'Szabadka': " + str(szabadka.count()))
    szabadka.first.click(timeout=10000)
    page.wait_for_timeout(1000)
    print("Клик по Szabadka выполнен")

    print("Шаг Г: ищу кнопку Ugytipus hozzaadasa")
    btn2 = page.locator("text=Ügytípus hozzáadása")
    print("Найдено кнопок 'Ügytípus hozzáadása': " + str(btn2.count()))
    btn2.first.click(timeout=10000)

    print("Шаг Д: жду появления модалки #modalCases")
    try:
        page.wait_for_selector("#modalCases.show", timeout=8000)
        print("Модалка #modalCases открылась")
    except Exception as e:
        print("Модалка #modalCases НЕ открылась: " + str(e))

    page.wait_for_timeout(500)

    print("Шаг Е: вывожу все label внутри modalCases")
    modal_labels = page.locator("#modalCases label")
    label_count = modal_labels.count()
    print("Всего label в modalCases: " + str(label_count))
    for i in range(min(label_count, 60)):
        try:
            txt = modal_labels.nth(i).inner_text()
            print("Label " + str(i) + ": [" + txt + "]")
        except Exception as e:
            print("Label " + str(i) + ": ошибка чтения " + str(e))

    visa = page.locator("label:has-text('Vízumkérelem (schengeni - C)')")
    print("Найдено label с точным текстом визы C: " + str(visa.count()))
    if visa.count() > 0:
        visa.first.click(timeout=10000)
        page.wait_for_timeout(500)
        print("Клик по Vízumkérelem (schengeni - C) выполнен")
    else:
        print("Точный вариант не найден - нужна ручная проверка списка выше")

    try:
        save = page.get_by_role("button", name="Mentés")
        print("Найдено кнопок Mentés: " + str(save.count()))
        if save.count() > 0:
            save.first.click(timeout=5000)
            page.wait_for_timeout(1000)
            print("Клик по Mentés выполнен")
    except Exception as e:
        print("Ошибка при клике Mentés: " + str(e))


def fill_form(page):
    page.wait_for_timeout(1000)

    inputs = page.locator(
        "input:visible:not([type=checkbox]):not([type=radio])"
    )

    count = inputs.count()
    print("Visible inputs: " + str(count))

    secret_names = [
        "VISA_NAME", "VISA_BIRTHDATE", "VISA_APPLICANTS_COUNT",
        "VISA_PHONE", "VISA_EMAIL", "VISA_RESIDENCE_PERMIT",
        "VISA_NATIONALITY", "VISA_PASSPORT", "VISA_RESIDENCE_COMMUNITY"
    ]
    for name in secret_names:
        val = os.environ.get(name, "")
        print(name + " задан: " + str(bool(val)) + ", длина: " + str(len(val)))

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

    value_index = 0

    for i in range(count):
        if value_index >= len(values):
            break

        value = values[value_index]

        if not value:
    value_index += 1
    continue


        try:
            inputs.nth(i).fill(value)
            value_index += 1
        except Exception:
            pass

    checkboxes = page.locator("input[type=checkbox]:visible")

    for i in range(checkboxes.count()):
        try:
            if not checkboxes.nth(i).is_checked():
                checkboxes.nth(i).check(force=True)
        except Exception:
            pass


def check_calendar_for_slots(page):
    content = page.content().lower()

    free_count = content.count("free")
    print("Найдено слово 'free' на странице: " + str(free_count) + " раз")

    markers = ["nincs szabad", "nincs elérhető", "no available"]
    has_slots = True
    found_marker = None
    for m in markers:
        if m in content:
            has_slots = False
            found_marker = m

    print("Проверка календаря: has_slots=" + str(has_slots))
    if found_marker:
        print("Найден маркер отсутствия слотов: '" + found_marker + "'")
    elif free_count > 0:
        print("ВНИМАНИЕ: слово 'free' встречается на странице - похоже, слоты реально есть!")

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
            try:
                page.keyboard.press("Escape")
                page.wait_for_timeout(500)
            except:
                pass

            try:
                save = page.get_by_role("button", name="Mentés")
                if save.count() > 0:
                    save.first.click(timeout=5000)
                    page.wait_for_timeout(1000)
            except:
                pass

            try:
                page.locator("button.btn-close").first.click(timeout=3000)
                page.wait_for_timeout(1000)
            except:
                pass

            try:
                page.locator("#modalCases").wait_for(
                    state="hidden",
                    timeout=10000
                )
            except:
                pass

            next_button = page.get_by_role(
                "button",
                name="Tovább az időpontválasztáshoz"
            )

            next_button.scroll_into_view_if_needed()

            next_button.click(
                force=True,
                timeout=15000
            )

            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(2000)

            safe_screenshot(page, "step4_calendar.png")

            page_check = page.content().lower()
            if "kitöltése szükséges" in page_check or "hibás" in page_check:
                print("Форма не прошла валидацию - переход к календарю НЕ состоялся")
                browser.close()
                return None

        except Exception as e:
            print(str(e))
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
            notify("‼️‼️ СЛОТ НАЙДЕН ‼️‼️ https://konzinfoidopont.mfa.gov.hu/")
        elif result is False:
            print("Слотов нет - уведомление не отправляется")
        else:
            print("Не удалось проверить (ошибка/незавершённая форма) - уведомление не отправляется")

    except Exception as e:
        print("Ошибка: " + str(e))
