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

    print("Шаг В: ищу label с текстом Belgrád")
    szabadka = page.locator("label:has-text('Belgrád')")
    print("Найдено label с 'Belgrád': " + str(szabadka.count()))
    szabadka.first.click(timeout=10000)
    page.wait_for_timeout(1000)
    print("Клик по Belgrád выполнен")

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


def xpath_literal(s):
    """Безопасно оборачивает строку для использования в XPath, даже если в ней есть кавычки."""
    if "'" not in s:
        return "'" + s + "'"
    if '"' not in s:
        return '"' + s + '"'
    parts = s.split("'")
    return "concat('" + "', \"'\", '".join(parts) + "')"


def fill_field_by_label(page, label_text, value):
    """
    Заполняет поле, находя его по подписи (label), а НЕ по порядковому номеру.
    Это устойчиво к любым сдвигам разметки, из-за которых значения
    могли "разъезжаться" по чужим полям.
    """
    if not value:
        return False

    # Стратегия 1: стандартная связка <label for="..."> с полем
    try:
        field = page.get_by_label(label_text, exact=True)
        if field.count() > 0:
            field.first.fill(value)
            print("Заполнено поле '" + label_text + "' (стандартная привязка label)")
            return True
    except Exception:
        pass

    # Стратегия 2: ищем элемент с точным текстом label, затем ближайший
    # видимый input в общем родительском контейнере (на 1 или 2 уровня выше)
    try:
        lit = xpath_literal(label_text)
        label_loc = page.locator(
            "xpath=//*[self::label or self::div or self::span][normalize-space(text())=" + lit + "]"
        )
        found_count = label_loc.count()
        if found_count > 0:
            for level in [1, 2, 3]:
                try:
                    row = label_loc.first.locator(
                        "xpath=ancestor::div[" + str(level) + "]"
                    )
                    input_in_row = row.locator("input:visible")
                    if input_in_row.count() > 0:
                        input_in_row.first.fill(value)
                        print(
                            "Заполнено поле '" + label_text
                            + "' (найдено рядом с label, уровень контейнера " + str(level) + ")"
                        )
                        return True
                except Exception:
                    continue
    except Exception as e:
        print("Ошибка при поиске поля по label '" + label_text + "': " + str(e))

    print("НЕ удалось найти поле для label '" + label_text + "' - значение НЕ записано")
    return False


def fill_form(page):
    page.wait_for_timeout(1000)

    secret_names = [
        "VISA_NAME", "VISA_BIRTHDATE", "VISA_APPLICANTS_COUNT",
        "VISA_PHONE", "VISA_EMAIL", "VISA_RESIDENCE_PERMIT",
        "VISA_NATIONALITY", "VISA_PASSPORT", "VISA_RESIDENCE_COMMUNITY"
    ]
    for name in secret_names:
        val = os.environ.get(name, "")
        print(name + " задан: " + str(bool(val)) + ", длина: " + str(len(val)))

    email = os.environ.get("VISA_EMAIL", "")

    # Точные подписи полей, как они видны на форме (важен порядок для лога, не для заполнения)
    label_value_pairs = [
        ("Név", os.environ.get("VISA_NAME", "")),
        ("Születési idő", os.environ.get("VISA_BIRTHDATE", "")),
        ("Kérelmezők száma", os.environ.get("VISA_APPLICANTS_COUNT", "1")),
        ("Értesítési telefonszám", os.environ.get("VISA_PHONE", "")),
        ("E-mail cím", email),
        ("E-mail cím újra", email),
        ("Szerb tartózkodási engedély száma, érvényessége", os.environ.get("VISA_RESIDENCE_PERMIT", "")),
        ("Állampolgárság", os.environ.get("VISA_NATIONALITY", "")),
        ("Útlevél száma", os.environ.get("VISA_PASSPORT", "")),
        ("Residential community in Serbia", os.environ.get("VISA_RESIDENCE_COMMUNITY", "")),
    ]

    results = {}
    for label_text, value in label_value_pairs:
        ok = fill_field_by_label(page, label_text, value)
        results[label_text] = ok

    not_filled = [lbl for lbl, ok in results.items() if not ok]
    if not_filled:
        print("ВНИМАНИЕ: не удалось заполнить поля: " + ", ".join(not_filled))
    else:
        print("Все поля с непустыми значениями успешно найдены и заполнены по label")

    checkboxes = page.locator("input[type=checkbox]:visible")
    for i in range(checkboxes.count()):
        try:
            if not checkboxes.nth(i).is_checked():
                checkboxes.nth(i).check(force=True)
        except Exception:
            pass


def check_no_slots_popup(page):
    """
    Проверяет реальный, подтверждённый сайтом индикатор отсутствия
    свободных мест. У этого элемента есть точный id="nocase"
    (обнаружено по логам реального прогона), это надёжнее, чем
    искать текст по всей странице.
    """
    try:
        nocase = page.locator("#nocase")
        if nocase.count() > 0:
            try:
                is_visible = nocase.first.is_visible()
            except Exception:
                is_visible = False
            text = ""
            try:
                text = nocase.first.inner_text().strip()
            except Exception:
                pass

            print("Элемент #nocase найден. Видим: " + str(is_visible) + ", текст: [" + text + "]")

            if is_visible and text:
                print("Подтверждено: элемент #nocase видим и содержит текст - мест нет")
                safe_screenshot(page, "step5_red_nocase_message.png")
                try:
                    ok_btn = page.get_by_role("button", name="Rendben")
                    if ok_btn.count() > 0:
                        ok_btn.first.click(timeout=3000)
                        page.wait_for_timeout(500)
                        print("Модалка 'нет мест' закрыта по кнопке Rendben")
                except Exception as e:
                    print("Не удалось закрыть модалку 'нет мест': " + str(e))
                return True
    except Exception as e:
        print("Ошибка при проверке #nocase: " + str(e))

    # Запасной вариант - поиск по тексту, если id вдруг поменяется
    try:
        popup = page.get_by_text("nincs szabad időpont", exact=False)
        if popup.count() > 0 and popup.first.is_visible():
            print("Обнаружено модальное окно с текстом об отсутствии свободных мест (запасной способ поиска)")
            safe_screenshot(page, "step5_red_nocase_message_fallback.png")
            try:
                ok_btn = page.get_by_role("button", name="Rendben")
                if ok_btn.count() > 0:
                    ok_btn.first.click(timeout=3000)
                    page.wait_for_timeout(500)
            except Exception:
                pass
            return True
    except Exception as e:
        print("Ошибка при запасной проверке текста 'нет мест': " + str(e))

    return False


def check_real_calendar_reached(page):
    """
    Проверяет, попали ли мы на реальную страницу выбора даты
    (это отдельный виджет: "Select a date", "Time period",
    либо индикатор шагов "Időpontválasztás" стал активным шагом).
    """
    try:
        if page.get_by_text("Select a date", exact=False).count() > 0:
            return True
        if page.get_by_text("Time period", exact=False).count() > 0:
            return True
    except Exception as e:
        print("Ошибка при проверке признаков реального календаря: " + str(e))
    return False


def wait_for_real_outcome(page, timeout_ms=12000):
    """
    КРИТИЧЕСКИ ВАЖНО: после клика по кнопке перехода сайт делает
    проверку слотов асинхронно (AJAX), результат появляется не мгновенно.
    Если проверить состояние сразу - попап "нет мест" ещё может быть не
    показан, из-за чего скрипт ошибочно решит "раз попапа нет - слоты есть".

    Эта функция ждёт (с опросом каждые 500мс, до timeout_ms), пока не
    произойдёт один из ДВУХ позитивных, подтверждённых исходов:
      - "no_slots"  -> появился попап с #nocase / текстом "нет мест"
      - "calendar"  -> реально открылся календарь (шаг 2)
    Если за отведённое время ничего из этого не произошло - "timeout".
    Возвращать "слоты есть" без реального подтверждения календаря нельзя.
    """
    waited = 0
    step_ms = 500
    while waited <= timeout_ms:
        if check_no_slots_popup(page):
            return "no_slots"
        if check_real_calendar_reached(page):
            return "calendar"
        page.wait_for_timeout(step_ms)
        waited += step_ms
    return "timeout"


def check_calendar_has_free_slots(page):
    """
    На реальной странице календаря свободные слоты помечены словом "Free".
    Используем ТОЛЬКО видимый текст страницы (inner_text), а не весь HTML,
    чтобы не ловить скрытые/неотрендеренные элементы.
    """
    try:
        visible_text = page.locator("body").inner_text()
    except Exception as e:
        print("Не удалось прочитать видимый текст body: " + str(e))
        visible_text = ""

    has_free = "free" in visible_text.lower()
    print("Проверка реального календаря: слово 'Free' найдено = " + str(has_free))

    if not has_free:
        print("Длина видимого текста страницы календаря: " + str(len(visible_text)))

    return has_free


def collect_validation_errors(page):
    """Собирает видимые сообщения об ошибках валидации формы (если есть)."""
    reasons = []
    error_selectors = [
        ".is-invalid:visible",
        ".invalid-feedback:visible",
        ".text-danger:visible",
        ".alert-danger:visible",
    ]
    for sel in error_selectors:
        try:
            errs = page.locator(sel)
            cnt = errs.count()
            for i in range(min(cnt, 10)):
                try:
                    t = errs.nth(i).inner_text().strip()
                    if t:
                        reasons.append(t)
                except Exception:
                    pass
        except Exception as e:
            print("Ошибка при проверке селектора ошибок " + sel + ": " + str(e))
    return reasons


def run():
    """
    Возвращает кортеж (status, reasons):
      status = True          -> слоты найдены (реальный календарь, слово "Free")
      status = False         -> слотов нет (либо модалка "nincs szabad időpont",
                                 либо реальный календарь без "Free")
      status = "unverified"  -> ни модалки, ни календаря не найдено -
                                 похоже форма не прошла валидацию, доверять
                                 результату НЕЛЬЗЯ
      status = None          -> техническая ошибка на более раннем шаге
    """
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
            return None, []

        try:
            fill_form(page)
            safe_screenshot(page, "step3_after_fill.png")
        except Exception as e:
            print("Ошибка на этапе заполнения формы: " + str(e))
            safe_screenshot(page, "error_step3.png")
            browser.close()
            return None, []

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

        except Exception as e:
            print(str(e))
            safe_screenshot(page, "error_step4.png")
            browser.close()
            return None, []

        # --- Определяем реальный исход ---
        # ВАЖНО: не решаем мгновенно. Ждём, пока не появится ОДИН из
        # подтверждённых исходов (попап "нет мест" или реальный календарь).
        outcome = wait_for_real_outcome(page, timeout_ms=12000)
        print("Итог ожидания результата: " + outcome)

        if outcome == "no_slots":
            safe_screenshot(page, "step5_no_slots_popup.png")
            browser.close()
            return False, []

        if outcome == "calendar":
            safe_screenshot(page, "step5_calendar_reached.png")
            print("Реальный переход на шаг 2 (календарь) подтверждён - считаем, что слоты ЕСТЬ")
            browser.close()
            return True, []

        # outcome == "timeout": ни попап, ни календарь не появились за отведённое время
        reasons = collect_validation_errors(page)
        if not reasons:
            reasons.append(
                "Истёк таймаут ожидания: не появился ни индикатор 'нет мест', "
                "ни признаки реального календаря"
            )
        print("Не удалось подтвердить исход: " + " | ".join(reasons))
        safe_screenshot(page, "step5_unverified.png")
        browser.close()
        return "unverified", reasons


if __name__ == "__main__":
    try:
        result, reasons = run()

        if result is True:
            notify("BEOGRAD: Naiden svobodnyi slot! https://konzinfoidopont.mfa.gov.hu/")
        elif result is False:
            notify("BEOGRAD: slotov net.")
        elif result == "unverified":
            msg = "⚠️ BEOGRAD: не удалось проверить - не удалось подтвердить ни отсутствие, ни наличие мест (форма могла не пройти валидацию)."
            if reasons:
                msg += " Возможные причины: " + "; ".join(reasons[:3])
            notify(msg)
        else:
            notify("BEOGRAD: proverka zavershilas s oshibkoi.")

    except Exception as e:
        notify("BEOGRAD: Oshibka - " + str(e))
