import random
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, ElementNotInteractableException,
    StaleElementReferenceException, ElementClickInterceptedException
)
from selenium.webdriver.common.keys import Keys
from browser_utils import scroll_page, make_screenshot

# Селекторы для основных интерактивных элементов
INTERACTIVE_SELECTORS = {
    "buttons": [
        "button",
        "a.btn",
        "a.button",
        "div.btn",
        "div.button",
        "a[role='button']",
        "div[role='button']",
        "span.btn",
        "a.link",
        ".call-to-action"
    ],
    "navigation": [
        "nav a",
        ".menu a",
        ".navbar a",
        ".navigation a",
        "header a",
        "footer a",
        ".nav-link",
        ".main-menu a"
    ],
    "forms": [
        "form",
        ".contact-form",
        ".feedback-form",
        ".search-form",
        "#contact-form"
    ],
    "inputs": [
        "input[type='text']",
        "input[type='email']",
        "input[type='tel']",
        "input[type='number']",
        "textarea"
    ],
    "tabs": [
        ".tabs .tab",
        ".tabbed-content .tab-title",
        ".tab-panel .tab-header",
        "ul.tabs li",
        "[role='tab']"
    ],
    "accordions": [
        ".accordion-header",
        ".collapse-header",
        ".accordion-button",
        ".accordion-trigger",
        "[data-toggle='collapse']"
    ]
}

# Типичные подразделы сайта для посещения
COMMON_SITE_SECTIONS = [
    "о нас", "о компании", "about", "контакты", "contacts",
    "услуги", "services", "продукция", "products",
    "цены", "прайс", "prices", "price", "тарифы",
    "доставка", "shipping", "оплата", "payment",
    "отзывы", "reviews", "партнеры", "partners",
    "blog", "блог", "новости", "news", "статьи", "articles",
    "faq", "вопросы", "questions", "помощь", "help"
]

# Данные для заполнения форм
FORM_DATA = {
    "name": ["Иван Петров", "Алексей Смирнов", "Екатерина Иванова", "Мария Соколова"],
    "email": ["test@example.com", "info@example.org", "contact@test.ru"],
    "phone": ["+7(123)456-78-90", "8(987)654-32-10", "8 800 123 45 67"],
    "message": [
        "Здравствуйте! Интересует дополнительная информация о ваших услугах.",
        "Добрый день, хотел бы узнать подробности о сотрудничестве.",
        "Меня заинтересовало ваше предложение. Как можно получить консультацию?",
        "Здравствуйте, интересует прайс-лист на услуги."
    ]
}


def is_same_domain(url1, url2):
    """
    Проверяет, принадлежат ли два URL одному домену

    Args:
        url1 (str): Первый URL
        url2 (str): Второй URL

    Returns:
        bool: True, если URL относятся к одному домену
    """
    import urllib.parse

    try:
        # Извлекаем домены из URL
        domain1 = urllib.parse.urlparse(url1).netloc
        domain2 = urllib.parse.urlparse(url2).netloc

        # Удаляем www. из имени домена для корректного сравнения
        domain1 = domain1.replace('www.', '')
        domain2 = domain2.replace('www.', '')

        return domain1 == domain2
    except:
        # В случае ошибки разбора URL, считаем домены разными
        return False


def is_yandex_url(url):
    """
    Проверяет, относится ли URL к Яндексу

    Args:
        url (str): URL для проверки

    Returns:
        bool: True, если URL принадлежит Яндексу
    """
    yandex_domains = ['ya.ru', 'yandex.ru', 'yandex.net', 'yandex.com']

    try:
        import urllib.parse
        domain = urllib.parse.urlparse(url).netloc
        domain = domain.replace('www.', '')

        # Проверяем, содержит ли домен одно из известных имен Яндекса
        for yandex_domain in yandex_domains:
            if yandex_domain in domain:
                return True

        return False
    except:
        return False


def interact_with_site(driver, stay_time=60, interaction_level='medium'):
    """
    Выполняет активное взаимодействие с элементами сайта

    Args:
        driver (webdriver): Экземпляр браузера
        stay_time (int): Минимальное время пребывания на сайте в секундах
        interaction_level (str): Уровень взаимодействия: 'low', 'medium', 'high'

    Returns:
        dict: Информация о взаимодействиях с сайтом
    """
    print("\n" + "=" * 50)
    print("АКТИВНОЕ ВЗАИМОДЕЙСТВИЕ С САЙТОМ")
    print("=" * 50)

    # Проверяем, не находимся ли мы на странице Яндекса
    current_url = driver.current_url
    if is_yandex_url(current_url):
        print(f"Обнаружено, что мы находимся на странице Яндекса: {current_url}")
        print("Переход на целевой сайт не был выполнен корректно. Невозможно продолжить взаимодействие.")
        return {
            "visited_pages": [current_url],
            "clicked_elements": 0,
            "filled_forms": 0,
            "screenshots": []
        }

    start_time = time.time()

    # Время взаимодействия в зависимости от уровня
    interaction_times = {
        'low': stay_time,
        'medium': max(stay_time, 90),
        'high': max(stay_time, 180)
    }

    max_time = interaction_times.get(interaction_level, stay_time)
    print(f"Планируемое время взаимодействия: {max_time} секунд")
    print(f"Текущий URL: {current_url}")

    # Сохраним главный URL для возможности возврата
    main_url = current_url

    interactions = {
        "visited_pages": [main_url],
        "clicked_elements": 0,
        "filled_forms": 0,
        "screenshots": []
    }

    # Сначала просмотрим текущую страницу
    total_height = driver.execute_script("return document.body.scrollHeight")
    scroll_page(driver, "down", 150, total_height)
    time.sleep(random.uniform(1, 3))

    # Сделаем скриншот начальной страницы
    screenshot_file = make_screenshot(driver, "start_page_")
    interactions["screenshots"].append(screenshot_file)

    # Основной цикл взаимодействия
    while time.time() - start_time < max_time:
        remaining_time = max_time - (time.time() - start_time)
        print(f"\nОсталось времени: {remaining_time:.1f} секунд")

        # Проверяем, не ушли ли мы с целевого сайта (например, на Яндекс)
        current_url = driver.current_url
        if is_yandex_url(current_url) or not is_same_domain(current_url, main_url):
            print(f"Обнаружен переход на внешний домен: {current_url}")
            print(f"Возвращаемся на основной сайт: {main_url}")
            try:
                driver.get(main_url)
                time.sleep(random.uniform(2, 4))

                # Проверяем, удалось ли вернуться
                if is_yandex_url(driver.current_url) or not is_same_domain(driver.current_url, main_url):
                    print("Не удалось вернуться на целевой сайт. Прекращаем взаимодействие.")
                    break
            except:
                print("Ошибка при попытке вернуться на основной сайт.")
                break

        # С определенной вероятностью выбираем тип действия
        action = random.choices(
            ["navigate", "click_button", "fill_form", "use_tabs", "go_back", "scroll"],
            weights=[0.3, 0.2, 0.15, 0.15, 0.1, 0.1],
            k=1
        )[0]

        try:
            if action == "navigate" and try_navigate_to_section(driver):
                interactions["clicked_elements"] += 1
                new_url = driver.current_url

                # Проверяем, что мы не перешли на Яндекс или другой внешний сайт
                if is_yandex_url(new_url) or not is_same_domain(new_url, main_url):
                    print(f"Навигация привела к переходу на внешний сайт: {new_url}")
                    print("Возвращаемся назад")
                    driver.back()
                    time.sleep(random.uniform(1, 3))
                else:
                    # Добавляем URL только если это новая страница на том же сайте
                    interactions["visited_pages"].append(new_url)
                    print(f"Переход на новую страницу: {new_url}")
                    time.sleep(random.uniform(2, 5))

                    # После перехода на новую страницу - прокрутка
                    scroll_page(driver, "down", 150, driver.execute_script("return document.body.scrollHeight"))
                    time.sleep(random.uniform(1, 3))

                    # Сделаем скриншот новой страницы
                    if random.random() < 0.5:  # 50% шанс на скриншот
                        screenshot_file = make_screenshot(driver, "nav_page_")
                        interactions["screenshots"].append(screenshot_file)

            elif action == "click_button" and try_click_random_button(driver):
                interactions["clicked_elements"] += 1
                time.sleep(random.uniform(1, 3))

                # Проверяем, что мы не перешли на Яндекс или другой внешний сайт
                new_url = driver.current_url
                if is_yandex_url(new_url) or not is_same_domain(new_url, main_url):
                    print(f"Клик привел к переходу на внешний сайт: {new_url}")
                    print("Возвращаемся назад")
                    driver.back()
                    time.sleep(random.uniform(1, 3))
                else:
                    # Если URL изменился после клика, добавим его
                    if new_url not in interactions["visited_pages"]:
                        interactions["visited_pages"].append(new_url)
                        print(f"URL после клика: {new_url}")

            elif action == "fill_form" and try_fill_random_form(driver):
                interactions["filled_forms"] += 1
                screenshot_file = make_screenshot(driver, "form_")
                interactions["screenshots"].append(screenshot_file)
                time.sleep(random.uniform(2, 4))

            elif action == "use_tabs" and try_interact_with_tabs_accordions(driver):
                interactions["clicked_elements"] += 1
                time.sleep(random.uniform(1, 3))

            elif action == "go_back" and len(interactions["visited_pages"]) > 1:
                print("Возвращаемся на предыдущую страницу")
                driver.back()
                time.sleep(random.uniform(1, 3))

                # Проверяем, вернулись ли мы на существующую страницу
                back_url = driver.current_url
                if is_yandex_url(back_url):
                    print(f"Возврат привел к переходу на Яндекс: {back_url}")
                    print(f"Переходим на основной сайт: {main_url}")
                    driver.get(main_url)
                    time.sleep(random.uniform(2, 4))

                # После возврата - прокрутка
                scroll_page(driver, "down", 150, driver.execute_script("return document.body.scrollHeight"))

            elif action == "scroll":
                print("Прокручиваем страницу для осмотра")
                direction = random.choice(["down", "up"])
                scroll_page(driver, direction, 150, driver.execute_script("return document.body.scrollHeight"))
                time.sleep(random.uniform(1, 2))

            else:
                # Если никакое действие не выполнилось, просто немного подождем
                print("Ожидание...")
                time.sleep(random.uniform(1, 3))

        except Exception as e:
            print(f"Ошибка при взаимодействии с сайтом: {str(e)}")
            time.sleep(random.uniform(1, 2))

    # В конце проверим, вернулись ли мы на главную страницу
    if driver.current_url != main_url:
        print("Возвращаемся на главную страницу сайта")
        try:
            driver.get(main_url)
            time.sleep(random.uniform(1, 3))
        except:
            print("Не удалось вернуться на главную страницу")

    # Финальный скриншот
    screenshot_file = make_screenshot(driver, "final_page_")
    interactions["screenshots"].append(screenshot_file)

    print("\n" + "=" * 50)
    print("ИТОГИ ВЗАИМОДЕЙСТВИЯ:")
    print(f"Посещено страниц: {len(interactions['visited_pages'])}")
    print(f"Нажато на элементы: {interactions['clicked_elements']}")
    print(f"Заполнено форм: {interactions['filled_forms']}")
    print(f"Сделано скриншотов: {len(interactions['screenshots'])}")
    print("=" * 50)

    return interactions


def try_navigate_to_section(driver):
    """
    Пытается найти и перейти на один из типичных разделов сайта

    Args:
        driver (webdriver): Экземпляр браузера

    Returns:
        bool: True, если удалось перейти на новую страницу
    """
    print("Поиск и переход в другой раздел сайта...")

    # Запоминаем текущий URL
    current_url = driver.current_url

    # Сначала ищем ссылки по тексту из распространенных разделов
    for section in random.sample(COMMON_SITE_SECTIONS, len(COMMON_SITE_SECTIONS)):
        try:
            # Пытаемся найти ссылку с текстом, содержащим название раздела
            links = driver.find_elements(By.XPATH,
                                         f"//a[contains(translate(text(), 'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ', 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'), '{section}')]")

            # Также ищем ссылки с атрибутом title или aria-label
            links.extend(driver.find_elements(By.XPATH,
                                              f"//a[contains(translate(@title, 'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ', 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'), '{section}')]"))
            links.extend(driver.find_elements(By.XPATH,
                                              f"//a[contains(translate(@aria-label, 'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ', 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'), '{section}')]"))

            # И по атрибуту href
            links.extend(driver.find_elements(By.XPATH, f"//a[contains(@href, '{section}')]"))

            # Отфильтровываем внешние ссылки
            internal_links = []
            for link in links:
                href = link.get_attribute("href")
                if href and "yandex" not in href and "ya.ru" not in href:
                    # Дополнительная проверка на относительную ссылку или ссылку на тот же домен
                    if href.startswith('/') or href.startswith('#') or is_same_domain(href, current_url):
                        internal_links.append(link)

            links = internal_links

            if links:
                # Выбираем случайную ссылку из найденных
                link = random.choice(links)
                if link.is_displayed() and link.is_enabled():
                    print(f"Переход в раздел '{section}'")

                    # Прокручиваем к ссылке
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", link)
                    time.sleep(random.uniform(0.5, 1.5))

                    # Сохраняем URL ссылки
                    href = link.get_attribute("href")

                    # Сначала пробуем JavaScript клик
                    try:
                        driver.execute_script("arguments[0].click();", link)
                    except:
                        # Если не сработало, пробуем обычный клик
                        link.click()

                    # Ждем изменения URL или загрузки страницы
                    try:
                        WebDriverWait(driver, 5).until(lambda d: d.current_url != current_url)
                    except:
                        pass

                    time.sleep(random.uniform(1, 3))  # Даем странице время загрузиться

                    # Проверяем, изменился ли URL и не перешли ли мы на Яндекс
                    new_url = driver.current_url
                    if new_url != current_url:
                        # Проверяем, что это не переход на Яндекс или другой внешний сайт
                        if is_yandex_url(new_url):
                            print(f"Переход привел на Яндекс: {new_url}")
                            print("Возвращаемся назад")
                            driver.back()
                            time.sleep(random.uniform(1, 2))
                            return False
                        return True

        except (StaleElementReferenceException, ElementClickInterceptedException, ElementNotInteractableException):
            continue
        except Exception as e:
            print(f"Ошибка при попытке перехода в раздел '{section}': {str(e)}")

    # Если не нашли по тексту, пробуем общие селекторы навигации
    for nav_selector in INTERACTIVE_SELECTORS["navigation"]:
        try:
            nav_elements = driver.find_elements(By.CSS_SELECTOR, nav_selector)

            # Фильтруем внешние ссылки
            internal_nav_elements = []
            for nav in nav_elements:
                href = nav.get_attribute("href")
                if href and "yandex" not in href and "ya.ru" not in href:
                    # Проверяем, что это внутренняя ссылка
                    if href.startswith('/') or href.startswith('#') or is_same_domain(href, current_url):
                        internal_nav_elements.append(nav)

            nav_elements = internal_nav_elements

            if nav_elements:
                # Берем случайный элемент из первых 5 (или сколько есть)
                nav_element = random.choice(nav_elements[:min(5, len(nav_elements))])
                if nav_element.is_displayed() and nav_element.is_enabled():
                    link_text = nav_element.text.strip() or "Неизвестный раздел"
                    print(f"Переход по навигационной ссылке: {link_text}")

                    # Прокручиваем к ссылке
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", nav_element)
                    time.sleep(random.uniform(0.5, 1.5))

                    # Пробуем клик разными способами
                    try:
                        driver.execute_script("arguments[0].click();", nav_element)
                    except:
                        try:
                            nav_element.click()
                        except:
                            continue

                    # Ждем изменения URL или загрузки страницы
                    try:
                        WebDriverWait(driver, 5).until(lambda d: d.current_url != current_url)
                    except:
                        pass

                    time.sleep(random.uniform(1, 3))

                    # Проверяем, изменился ли URL
                    new_url = driver.current_url
                    if new_url != current_url:
                        # Проверяем, что это не переход на Яндекс или другой внешний сайт
                        if is_yandex_url(new_url):
                            print(f"Переход привел на Яндекс: {new_url}")
                            print("Возвращаемся назад")
                            driver.back()
                            time.sleep(random.uniform(1, 2))
                            return False
                        return True
        except:
            continue

    print("Не удалось найти и перейти в другой раздел сайта")
    return False


def try_click_random_button(driver):
    """
    Находит и кликает на случайную кнопку или интерактивный элемент

    Args:
        driver (webdriver): Экземпляр браузера

    Returns:
        bool: True, если успешно кликнули на элемент
    """
    print("Поиск и клик на интерактивные элементы...")

    # Запоминаем текущий URL
    current_url = driver.current_url

    for selector in INTERACTIVE_SELECTORS["buttons"]:
        try:
            buttons = driver.find_elements(By.CSS_SELECTOR, selector)
            if not buttons:
                continue

            # Фильтруем видимые элементы и исключаем внешние ссылки
            visible_buttons = []
            for btn in buttons:
                if not (btn.is_displayed() and btn.is_enabled()):
                    continue

                # Проверяем, не является ли кнопка ссылкой на внешний ресурс
                href = btn.get_attribute("href")
                if href and ("yandex" in href or "ya.ru" in href):
                    continue

                # Проверяем, что это внутренняя ссылка или не ссылка вообще
                if not href or href.startswith('/') or href.startswith('#') or is_same_domain(href, current_url):
                    visible_buttons.append(btn)

            if not visible_buttons:
                continue

            # Выбираем случайную кнопку
            button = random.choice(visible_buttons)
            button_text = button.text.strip() or button.get_attribute("title") or button.get_attribute(
                "aria-label") or "Неизвестная кнопка"

            # Избегаем кнопок, связанных с отправкой форм
            if "submit" in button.get_attribute("type",
                                                "") or "отправить" in button_text.lower() or "submit" in button_text.lower():
                continue

            print(f"Клик на элемент: {button_text}")

            # Прокручиваем к кнопке
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
            time.sleep(random.uniform(0.5, 1.5))

            # Проверяем, не откроет ли клик новое окно
            will_open_new_window = button.get_attribute("target") == "_blank"

            # Пробуем разные способы клика
            try:
                driver.execute_script("arguments[0].click();", button)
            except:
                try:
                    button.click()
                except:
                    continue

            time.sleep(random.uniform(1, 3))

            # Обрабатываем возможные всплывающие окна или диалоги
            try:
                # Если появился alert, принимаем его
                alert = driver.switch_to.alert
                alert.accept()
            except:
                pass

            # Если открылось новое окно, переключаемся обратно
            if will_open_new_window:
                try:
                    if len(driver.window_handles) > 1:
                        print("Закрываем новое окно и возвращаемся к основному")
                        driver.switch_to.window(driver.window_handles[1])
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                except:
                    pass

            # Проверяем, не перешли ли мы на Яндекс
            new_url = driver.current_url
            if is_yandex_url(new_url):
                print(f"Клик привел к переходу на Яндекс: {new_url}")
                print("Возвращаемся назад")
                driver.back()
                time.sleep(random.uniform(1, 2))
                return False

            return True

        except (StaleElementReferenceException, ElementClickInterceptedException, ElementNotInteractableException):
            continue
        except Exception as e:
            print(f"Ошибка при клике на элемент: {str(e)}")

    print("Не удалось найти и кликнуть на интерактивный элемент")
    return False


def try_fill_random_form(driver):
    """
    Ищет на странице форму и заполняет её случайными данными

    Args:
        driver (webdriver): Экземпляр браузера

    Returns:
        bool: True, если форма найдена и заполнена
    """
    print("Поиск и заполнение формы...")

    # Сначала ищем форму
    form_element = None
    for selector in INTERACTIVE_SELECTORS["forms"]:
        try:
            forms = driver.find_elements(By.CSS_SELECTOR, selector)
            if forms:
                # Берем форму с наибольшим количеством полей
                form_element = max(forms, key=lambda form: len(form.find_elements(By.TAG_NAME, "input")))
                break
        except:
            continue

    if not form_element:
        print("Форма не найдена")
        return False

    print("Форма найдена, начинаем заполнение")

    # Находим поля для заполнения
    filled_fields = 0

    # Обрабатываем текстовые поля
    for input_selector in INTERACTIVE_SELECTORS["inputs"]:
        try:
            inputs = form_element.find_elements(By.CSS_SELECTOR, input_selector)
            for input_field in inputs:
                if not input_field.is_displayed() or not input_field.is_enabled():
                    continue

                # Пропускаем скрытые поля, чекбоксы и радио-кнопки
                field_type = input_field.get_attribute("type")
                if field_type in ["hidden", "checkbox", "radio", "submit", "button", "file"]:
                    continue

                # Пропускаем уже заполненные поля
                if input_field.get_attribute("value"):
                    continue

                # Определяем тип поля и подходящие данные
                field_name = input_field.get_attribute("name") or ""
                field_id = input_field.get_attribute("id") or ""
                field_placeholder = input_field.get_attribute("placeholder") or ""

                combined_field_info = (field_name + field_id + field_placeholder).lower()

                # Выбираем подходящие данные
                value = ""
                if any(word in combined_field_info for word in ["name", "имя", "фамилия", "firstname", "lastname"]):
                    value = random.choice(FORM_DATA["name"])
                elif any(word in combined_field_info for word in ["email", "почта", "mail"]):
                    value = random.choice(FORM_DATA["email"])
                elif any(word in combined_field_info for word in ["phone", "телефон", "тел", "моб"]):
                    value = random.choice(FORM_DATA["phone"])
                elif any(word in combined_field_info for word in
                         ["message", "сообщение", "comment", "комментарий", "вопрос", "question"]):
                    value = random.choice(FORM_DATA["message"])
                else:
                    # Для неопознанных полей используем имя
                    value = random.choice(FORM_DATA["name"])

                # Прокручиваем к полю
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", input_field)
                time.sleep(random.uniform(0.5, 1.0))

                # Очищаем поле и заполняем данными
                input_field.clear()
                for char in value:
                    input_field.send_keys(char)
                    time.sleep(random.uniform(0.05, 0.15))

                print(f"Заполнено поле ({field_name or field_id}): {value}")
                filled_fields += 1
                time.sleep(random.uniform(0.5, 1.0))
        except Exception as e:
            print(f"Ошибка при заполнении поля формы: {str(e)}")

    # Обрабатываем чекбоксы (обычно согласие с правилами)
    try:
        checkboxes = form_element.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
        for checkbox in checkboxes:
            if checkbox.is_displayed() and checkbox.is_enabled() and not checkbox.is_selected():
                # Если это согласие с правилами или обработкой персональных данных, отмечаем
                checkbox_id = checkbox.get_attribute("id") or ""
                checkbox_name = checkbox.get_attribute("name") or ""

                if any(word in (checkbox_id + checkbox_name).lower() for word in
                       ["agree", "consent", "policy", "согласие", "политик"]):
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", checkbox)
                    time.sleep(random.uniform(0.5, 1.0))

                    # Используем JavaScript для безопасного клика
                    driver.execute_script("arguments[0].click();", checkbox)
                    print("Отмечен чекбокс согласия")
                    time.sleep(random.uniform(0.5, 1.0))
    except Exception as e:
        print(f"Ошибка при обработке чекбоксов: {str(e)}")

    print(f"Форма заполнена ({filled_fields} полей)")

    # Принимаем решение об отправке формы (с низкой вероятностью)
    if random.random() < 0.1:  # Вероятность 10%
        try:
            # Ищем кнопку отправки формы
            submit_buttons = form_element.find_elements(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
            if not submit_buttons:
                submit_buttons = form_element.find_elements(By.XPATH,
                                                            "//button[contains(text(), 'Отправить') or contains(text(), 'Submit') or contains(text(), 'Send')]")

            if submit_buttons:
                print("Форма готова к отправке, но отправка отключена в целях тестирования")
                # Можно раскомментировать для реальной отправки:
                # submit_button = submit_buttons[0]
                # driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_button)
                # time.sleep(random.uniform(0.5, 1.0))
                # driver.execute_script("arguments[0].click();", submit_button)
                # print("Форма отправлена")
                # time.sleep(random.uniform(2, 4))
        except Exception as e:
            print(f"Ошибка при отправке формы: {str(e)}")

    return filled_fields > 0


def try_interact_with_tabs_accordions(driver):
    """
    Взаимодействует с табами и аккордеонами на странице

    Args:
        driver (webdriver): Экземпляр браузера

    Returns:
        bool: True, если успешно взаимодействовали с элементом
    """
    print("Поиск и взаимодействие с табами и аккордеонами...")

    # Сохраняем текущий URL для проверки
    current_url = driver.current_url

    # Сначала попробуем табы
    for tab_selector in INTERACTIVE_SELECTORS["tabs"]:
        try:
            tabs = driver.find_elements(By.CSS_SELECTOR, tab_selector)
            if tabs:
                visible_tabs = [tab for tab in tabs if tab.is_displayed() and tab.is_enabled()]
                if visible_tabs:
                    tab = random.choice(visible_tabs)
                    tab_text = tab.text.strip() or "Таб"

                    print(f"Клик на таб: {tab_text}")

                    # Прокручиваем к табу
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", tab)
                    time.sleep(random.uniform(0.5, 1.5))

                    # Пробуем клик
                    try:
                        driver.execute_script("arguments[0].click();", tab)
                    except:
                        tab.click()

                    time.sleep(random.uniform(1, 3))

                    # Проверяем, не перешли ли мы на Яндекс или другой сайт
                    new_url = driver.current_url
                    if is_yandex_url(new_url) or not is_same_domain(new_url, current_url):
                        print(f"Взаимодействие привело к переходу на внешний сайт: {new_url}")
                        print("Возвращаемся назад")
                        driver.back()
                        time.sleep(random.uniform(1, 2))
                        return False

                    return True
        except Exception as e:
            print(f"Ошибка при взаимодействии с табами: {str(e)}")

    # Если не нашли табы, пробуем аккордеоны
    for accordion_selector in INTERACTIVE_SELECTORS["accordions"]:
        try:
            accordions = driver.find_elements(By.CSS_SELECTOR, accordion_selector)
            if accordions:
                visible_accordions = [acc for acc in accordions if acc.is_displayed() and acc.is_enabled()]
                if visible_accordions:
                    accordion = random.choice(visible_accordions)
                    accordion_text = accordion.text.strip() or "Аккордеон"

                    print(f"Клик на аккордеон: {accordion_text}")

                    # Прокручиваем к аккордеону
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", accordion)
                    time.sleep(random.uniform(0.5, 1.5))

                    # Пробуем клик
                    try:
                        driver.execute_script("arguments[0].click();", accordion)
                    except:
                        accordion.click()

                    time.sleep(random.uniform(1, 3))

                    # Проверяем, не перешли ли мы на Яндекс или другой сайт
                    new_url = driver.current_url
                    if is_yandex_url(new_url) or not is_same_domain(new_url, current_url):
                        print(f"Взаимодействие привело к переходу на внешний сайт: {new_url}")
                        print("Возвращаемся назад")
                        driver.back()
                        time.sleep(random.uniform(1, 2))
                        return False

                    return True
        except Exception as e:
            print(f"Ошибка при взаимодействии с аккордеонами: {str(e)}")

    print("Не найдены табы или аккордеоны для взаимодействия")
    return False