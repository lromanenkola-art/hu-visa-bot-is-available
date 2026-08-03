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


def notify_with_photo(text, photo_path):
    token = os.environ["TG_TOKEN"]
    chat_id = os.environ["TG_CHAT_ID"]

    try:
        with open(photo_path, "rb") as f:
            response = requests.post(
                f"https://api.telegram.org/bot{token}/sendPhoto",
                data={"chat_id": chat_id, "caption": text},
                files={"photo": f}
            )
        print("Telegram photo status:", response.status_code)
        print("Telegram photo response:", response.text)
    except Exception as e:
        print("Не удалось отправить фото: " + str(e))
        notify(text)


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

    print("Шаг В: ищу label с текстом Belgrad")
    belgrad = page.locator("label:has-text('Belgrád')")
    print("Найдено label с 'Belgrád': " + str(belgrad.count()))
    belgrad.first.click(timeout=10000)
    page.wait_for_timeout(1000)
    print("Клик по Belgrad выполнен")

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

    visa = page.locator("label:has-text('schengeni')")
    print("Найдено label со словом 'schengeni': " + str(visa.count()))
    if visa.count() > 0:
        visa.first.click(timeout=10000)
        page.wait_for_timeout(500)
        print("Клик по visa (schengeni) выполнен")
    else:
        print("Вариант с 'schengeni' не найден - нужна ручная проверка списка выше")

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

    # Дополнительная подстраховка: принудительно перезаписываем
    # дату рождения и телефон по надёжному поиску через placeholder,
    # так как эти поля чаще всего вызывали ошибку валидации.
    try:
        birthdate_field = page.get_by_placeholder("pl. 1990.01.30.")
        if birthdate_field.count() > 0:
            birthdate_field.first.fill(os.environ.get("VISA_BIRTHDATE", ""))
            print("Дата рождения перепроверена/перезаписана по placeholder")
    except Exception as e:
        print("Не удалось перезаписать дату рождения по placeholder: " + str(e))

    try:
        phone_field = page.get_by_placeholder("pl. +3612345678")
        if phone_field.count() > 0:
            phone_field.first.fill(os.environ.get("VISA_PHONE", ""))
            print("Телефон перепроверен/перезаписан по placeholder")
    except Exception as e:
        print("Не удалось перезаписать телефон по placeholder: " + str(e))

    checkboxes = page.locator("input[type=checkbox]:visible")

    for i in range(checkboxes.count()):
        try:
            if not checkboxes.nth(i).is_checked():
                checkboxes.nth(i).check(force=True)
        except Exception:
            pass


def check_calendar_for_slots(page):
    try:
        visible_text = page.locator("body").inner_text().lower()
        print("Используется видимый текст страницы (inner_text)")
    except Exception as e:
        print("Не удалось получить видимый текст, использую весь HTML: " + str(e))
        visible_text = page.content().lower()

    free_count = visible_text.count("free")
    print("Найдено слово 'free' в ВИДИМОМ тексте: " + str(free_count) + " раз")

    markers = ["nincs szabad", "nincs elérhető", "no available"]
    has_slots = True
    found_marker = None
    for m in markers:
        if m in visible_text:
            has_slots = False
            found_marker = m

    print("Проверка календаря: has_slots=" + str(has_slots))
    if found_marker:
        print("Найден маркер отсутствия слотов (в видимом тексте): '" + found_marker + "'")
    elif free_count > 0:
        print("ВНИМАНИЕ: слово 'free' видно на странице - похоже, слоты реально есть!")

    return has_slots


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
            ]
        )
        page = browser.new_page(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 900}
        )
        page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        page.on("console", lambda msg: print("BROWSER CONSOLE [" + msg.type + "]: " + msg.text))
        page.on("pageerror", lambda exc: print("BROWSER PAGE ERROR: " + str(exc)))
        page.on(
            "response",
            lambda resp: print(
                "RESPONSE " + str(resp.status) + " " + resp.url
            ) if "konzinfoidopont" in resp.url or "api" in resp.url.lower() else None
        )
        page.on(
            "requestfailed",
            lambda req: print(
                "REQUEST FAILED: " + req.url + " - " + str(req.failure)
            )
        )

        try:
            page.goto("https://konzinfoidopont.mfa.gov.hu/", timeout=60000)
        except Exception as e:
            print("Первая попытка открыть сайт не удалась: " + str(e))
            print("Пробую ещё раз через 5 секунд...")
            page.wait_for_timeout(5000)
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

            # Диагностика: смотрим, что реально осталось в текстовых
            # полях после заполнения - чтобы в логах сразу было видно,
            # если какое-то поле не заполнилось как надо
            try:
                check_inputs = page.locator(
                    "input:visible:not([type=checkbox]):not([type=radio])"
                )
                for i in range(check_inputs.count()):
                    try:
                        val = check_inputs.nth(i).input_value()
                        print("Проверка поля #" + str(i) + ": '" + val + "'")
                    except Exception as e:
                        print("Не удалось прочитать поле #" + str(i) + ": " + str(e))
            except Exception as e:
                print("Не удалось проверить заполненные поля: " + str(e))

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

            try:
                is_disabled = next_button.first.is_disabled()
                print("Кнопка 'Tovább' disabled=" + str(is_disabled))
            except Exception as e:
                print("Не удалось проверить disabled у кнопки: " + str(e))

            # Сначала пробуем настоящий клик мышью - если что-то перекрывает
            # кнопку, Playwright сообщит об этом явно (без force это видно)
            click_succeeded = False
            try:
                next_button.click(timeout=5000)
                click_succeeded = True
                print("Обычный клик по кнопке сработал")
            except Exception as e:
                print("Обычный клик не сработал (возможно, кнопка чем-то перекрыта): " + str(e))

            if not click_succeeded:
                # Кликаем напрямую через JS - это вызывает click() прямо на
                # DOM-элементе кнопки, минуя реальное позиционирование мыши,
                # поэтому не важно, перекрыт ли элемент чем-то визуально
                try:
                    next_button.first.evaluate("el => el.click()")
                    click_succeeded = True
                    print("JS-клик (el.click()) по кнопке выполнен")
                except Exception as e:
                    print("JS-клик тоже не сработал: " + str(e))
                    # Последняя попытка - старый способ через force
                    next_button.click(force=True, timeout=15000)
                    print("Резервный force-клик выполнен")

            page.wait_for_load_state("networkidle", timeout=20000)
            page.wait_for_timeout(4000)

            safe_screenshot(page, "step4_calendar.png")

            page_text = page.locator("body").inner_text().lower()

            # Проверяем модалку "нет свободных слотов" - это НЕ ошибка,
            # а нормальный ответ сайта, просто без перехода к календарю.
            # Реальный текст модалки:
            # "Tájékoztatjuk, hogy jelenleg nincs szabad időpont. Kérjük,
            #  vegye fel a kapcsolatot az illetékes külképviselettel /
            #  ügyfélszolgálattal."
            no_slots_markers = [
                "nincs szabad időpont",
                "nincs szabad",
                "nincs elérhető"
            ]
            if any(m in page_text for m in no_slots_markers):
                print("Белград: обнаружена модалка 'нет свободных мест' - слотов нет")
                # Отдельный скриншот именно в момент обнаружения модалки -
                # step4_calendar.png мог быть сделан чуть раньше, до того
                # как модалка полностью отрисовалась (анимация/fade-in)
                page.wait_for_timeout(500)
                safe_screenshot(page, "step5_no_slots_modal.png")
                try:
                    ok_btn = page.get_by_role("button", name="Rendben")
                    if ok_btn.count() > 0:
                        ok_btn.first.click(timeout=3000)
                except Exception:
                    pass
                browser.close()
                return False

            if "kitöltése szükséges" in page_text or "hibás" in page_text:
                print("Белград: форма не прошла валидацию - переход к календарю НЕ состоялся")
                browser.close()
                return None

            # Третий возможный исход: ни модалки "нет слотов", ни ошибки
            # валидации нет, но и календарь мог не открыться (например,
            # кнопка "тихо" осталась disabled). Проверяем явно.
            try:
                page.wait_for_selector("text=Time period", timeout=12000)
                print("Белград: подтверждено, страница календаря открыта")
            except Exception as e:
                print(
                    "Белград: календарь НЕ открылся и модалка 'нет слотов' не найдена: "
                    + str(e)
                )
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
            notify_with_photo(
                "‼️‼️ БЕЛГРАД: СЛОТ НАЙДЕН ‼️‼️ https://konzinfoidopont.mfa.gov.hu/",
                "step4_calendar.png"
            )
        elif result is False:
            print("Белград: слотов нет - уведомление не отправляется")
        else:
            print("Белград: не удалось проверить (ошибка/незавершённая форма)")
            notify("⚠️ Белград: бот не смог проверить сайт в этот раз (техническая накладка). Возможно, стоит проверить вручную.")

    except Exception as e:
        print("Белград: ошибка - " + str(e))
