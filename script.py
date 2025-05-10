import time
import random
import argparse
from urllib.parse import quote_plus
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager

# Список User-Agent для имитации разных браузеров
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
]


def get_random_user_agent():
    """Возвращает случайный User-Agent из списка"""
    return random.choice(USER_AGENTS)


def setup_browser(headless=False):
    """
    Настраивает и возвращает экземпляр браузера

    Args:
        headless (bool): Запускать ли браузер в фоновом режиме

    Returns:
        webdriver: Экземпляр браузера
    """
    options = Options()
    if headless:
        options.add_argument("--headless")

    # Установка случайного User-Agent
    user_agent = get_random_user_agent()
    options.add_argument(f'user-agent={user_agent}')

    # Дополнительные настройки для более эффективного обхода защиты от ботов
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    # Добавляем настройки для имитации обычного браузера
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-notifications")

    print("Запуск браузера...")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    # Более реалистичный размер окна
    driver.set_window_size(1920, 1080)

    # Скрытие признаков автоматизации
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.execute_script("delete navigator.__proto__.webdriver")

    # Эмуляция действий реального пользователя перед основными операциями
    print("Имитация поведения обычного пользователя...")
    try:
        # Перейдем сначала на другой сайт, чтобы имитировать обычное поведение
        driver.get("https://ya.ru")
        time.sleep(random.uniform(2, 4))

        # Выполним случайную прокрутку страницы
        driver.execute_script(f"window.scrollTo(0, {random.randint(100, 300)});")
        time.sleep(random.uniform(0.5, 1.5))
    except Exception as e:
        print(f"Ошибка при имитации обычного поведения: {str(e)}")

    return driver


def check_and_solve_captcha(driver):
    """
    Проверяет наличие капчи и пытается её решить

    Args:
        driver (webdriver): Экземпляр браузера

    Returns:
        bool: True, если капчи не было или она была успешно решена, False если не удалось решить
    """
    # Проверяем наличие различных вариантов капчи Яндекса
    captcha_selectors = [
        "//div[contains(text(), 'Подтвердите, что запросы отправляете вы, а не робот')]",
        "//div[contains(@class, 'CheckboxCaptcha-Anchor')]",
        "//div[contains(@class, 'AdvancedCaptcha-Anchor')]",
        "//iframe[contains(@src, 'captcha')]",
        "//input[contains(@class, 'CheckboxCaptcha-Button')]",
        "//input[@id='js-button']",
        "//div[contains(text(), 'Вы робот?')]",
        "//div[contains(@class, 'Captcha')]"
    ]

    captcha_found = False

    for selector in captcha_selectors:
        try:
            captcha_element = driver.find_element(By.XPATH, selector)
            if captcha_element.is_displayed():
                captcha_found = True
                print("\n" + "!" * 50)
                print("ОБНАРУЖЕНА КАПЧА!")
                print("!" * 50)

                # Пытаемся автоматически решить капчу
                if try_solve_checkbox_captcha(driver):
                    print("Капча успешно решена, продолжаем...")
                    return True
                else:
                    # Если автоматическое решение не сработало, просим пользователя
                    input(
                        "Не удалось автоматически решить капчу. Пожалуйста, решите капчу вручную в открытом браузере и нажмите Enter для продолжения...")

                print("Проверяем результаты после решения капчи...")
                time.sleep(3)  # Дополнительное время для загрузки результатов
                return True
        except NoSuchElementException:
            continue

    return not captcha_found  # Если капчи не было, возвращаем True


def try_solve_checkbox_captcha(driver):
    """
    Пытается автоматически решить капчу с чекбоксом

    Args:
        driver (webdriver): Экземпляр браузера

    Returns:
        bool: True, если капча была решена успешно, False в противном случае
    """
    print("\nПопытка автоматического решения капчи с чекбоксом...")

    try:
        # Пытаемся найти чекбокс по разным селекторам
        checkbox_selectors = [
            "//input[contains(@class, 'CheckboxCaptcha-Button')]",
            "//input[@id='js-button']",
            "//div[contains(@class, 'CheckboxCaptcha-Anchor')]",
            "//div[contains(@class, 'Checkbox-Anchor')]",
            "//div[@role='checkbox']",
            "//input[@role='checkbox']"
        ]

        for selector in checkbox_selectors:
            try:
                checkbox = driver.find_element(By.XPATH, selector)
                if checkbox.is_displayed():
                    print(f"Найден чекбокс: {selector}")

                    # Имитируем человеческое поведение перед кликом
                    # Сначала наведем мышь немного рядом с чекбоксом
                    action = webdriver.ActionChains(driver)

                    # Прокрутим страницу к чекбоксу
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});",
                                          checkbox)
                    time.sleep(random.uniform(0.5, 1.2))

                    # Случайное движение мыши вокруг чекбокса
                    action.move_to_element_with_offset(checkbox, random.randint(-20, 20), random.randint(-20, 20))
                    action.pause(random.uniform(0.3, 0.7))
                    action.move_to_element(checkbox)
                    action.pause(random.uniform(0.2, 0.5))

                    # Теперь кликаем на чекбокс
                    print("Кликаем на чекбокс капчи...")

                    # Вариант 1: Кликаем через ActionChains
                    action.click()
                    action.perform()

                    # Ждем немного
                    time.sleep(random.uniform(1.0, 2.0))

                    # Проверяем, исчезла ли капча
                    try:
                        # Проверяем наличие элементов, которые появляются после успешного решения
                        success_indicators = [
                            "//li[contains(@class, 'serp-item')]",  # Результаты поиска
                            "//div[contains(@class, 'CheckboxCaptcha-Success')]",  # Индикатор успеха
                            "//div[contains(text(), 'Спасибо')]",  # Текст благодарности
                        ]

                        for indicator in success_indicators:
                            if len(driver.find_elements(By.XPATH, indicator)) > 0:
                                print("Капча успешно решена автоматически!")
                                return True

                        # Если индикаторы не найдены, попробуем вариант 2: JavaScript клик
                        print("Первый способ не сработал, пробуем JavaScript клик...")
                        driver.execute_script("arguments[0].click();", checkbox)
                        time.sleep(random.uniform(1.0, 2.0))

                        # Снова проверяем успех
                        for indicator in success_indicators:
                            if len(driver.find_elements(By.XPATH, indicator)) > 0:
                                print("Капча успешно решена автоматически (JavaScript клик)!")
                                return True

                        # Если это тоже не сработало, используем дополнительные методы
                        print("JavaScript клик не сработал, пробуем Space и Enter...")

                        # Вариант 3: Фокус + Space или Enter
                        checkbox.send_keys(Keys.SPACE)
                        time.sleep(random.uniform(0.5, 1.0))

                        # Снова проверяем успех
                        for indicator in success_indicators:
                            if len(driver.find_elements(By.XPATH, indicator)) > 0:
                                print("Капча успешно решена автоматически (Space)!")
                                return True

                        # Последняя попытка с Enter
                        checkbox.send_keys(Keys.ENTER)
                        time.sleep(random.uniform(0.5, 1.0))

                        # Финальная проверка
                        for indicator in success_indicators:
                            if len(driver.find_elements(By.XPATH, indicator)) > 0:
                                print("Капча успешно решена автоматически (Enter)!")
                                return True

                        print("Автоматическое решение не сработало, требуется ручное вмешательство.")
                        return False

                    except Exception as e:
                        print(f"Ошибка при проверке решения капчи: {str(e)}")
                        return False
            except NoSuchElementException:
                continue

        print("Не найден подходящий чекбокс для автоматического решения капчи.")
        return False

    except Exception as e:
        print(f"Ошибка при попытке решить капчу: {str(e)}")
        return False


def search_yandex(driver, query, target_domain, num_pages=3):
    """
    Выполняет поиск в Яндексе и ищет указанный домен в результатах

    Args:
        driver (webdriver): Экземпляр браузера
        query (str): Поисковый запрос
        target_domain (str): Домен, который нужно найти
        num_pages (int): Количество страниц поиска для проверки

    Returns:
        dict: Информация о найденном результате (позиция, URL, заголовок)
    """
    results = []
    position = 0

    # Открываем страницу Яндекса
    print("Открываем Яндекс...")
    driver.get("https://ya.ru")
    time.sleep(random.uniform(1, 3))

    # Находим поисковую строку и вводим запрос
    print(f"Вводим поисковый запрос: {query}")
    try:
        search_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "text"))
        )

        # Имитация ввода текста с задержками, как настоящий пользователь
        for char in query:
            search_field.send_keys(char)
            time.sleep(random.uniform(0.05, 0.2))

        # Нажимаем клавишу Enter для выполнения поиска
        print("Выполняем поиск...")
        search_field.submit()

        # Проверяем наличие капчи
        time.sleep(2)  # Даем время для загрузки страницы

        # Проверяем и решаем капчу, если она появилась
        check_and_solve_captcha(driver)

        # Ждем загрузки результатов поиска
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "li.serp-item"))
            )
        except TimeoutException:
            print("Не удалось обнаружить результаты поиска по стандартному селектору. Проверяем альтернативные...")

            # Проверяем альтернативные селекторы для результатов поиска
            alternative_selectors = [
                "div.serp-item", "div.organic", "div[data-fast-name='organic']"
            ]

            for selector in alternative_selectors:
                try:
                    if len(driver.find_elements(By.CSS_SELECTOR, selector)) > 0:
                        print(f"Обнаружены результаты поиска по селектору: {selector}")
                        break
                except:
                    continue

            # Еще одна проверка - возможно мы уже на странице результатов, но селектор другой
            if "search" in driver.current_url:
                print("Мы находимся на странице результатов поиска. Продолжаем...")
            else:
                print("Мы не на странице результатов поиска. Проверьте браузер вручную.")
                input("Нажмите Enter для продолжения после исправления проблемы...")

    except TimeoutException:
        print("Не удалось найти поисковую строку или выполнить поиск")
        return None

    # Проверяем страницы результатов поиска
    for page in range(num_pages):
        if page > 0:
            print(f"Переход на страницу {page + 1} результатов...")
            try:
                # Находим кнопку перехода на следующую страницу
                next_page_selectors = [
                    f"a[aria-label='Страница {page + 1}']",
                    f"//a[contains(@aria-label, 'Страница {page + 1}')]",
                    "//a[contains(@class, 'Pager-Item_type_next')]",
                    "//a[contains(@data-fast-name, 'next')]",
                    "//div[contains(@class, 'pager')]//a[contains(text(), 'дальше')]",
                    "//div[contains(@class, 'pager')]//a[contains(text(), 'следующая')]"
                ]

                next_page = None
                for selector in next_page_selectors:
                    try:
                        if selector.startswith('//'):
                            elements = driver.find_elements(By.XPATH, selector)
                        else:
                            elements = driver.find_elements(By.CSS_SELECTOR, selector)

                        if elements and len(elements) > 0:
                            next_page = elements[0]
                            print(f"Найдена кнопка следующей страницы по селектору: {selector}")
                            break
                    except:
                        continue

                if not next_page:
                    print("Не удалось найти кнопку перехода на следующую страницу.")
                    break

                # Прокручиваем страницу вниз для лучшей видимости кнопки
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_page)
                time.sleep(random.uniform(0.5, 1.5))

                # Кликаем на кнопку следующей страницы
                next_page.click()

                # Проверяем наличие капчи после клика на следующую страницу
                time.sleep(2)  # Даем время для загрузки страницы или капчи
                print("Проверяем наличие капчи после перехода на следующую страницу...")
                if not check_and_solve_captcha(driver):
                    # Если после решения капчи мы не вернулись на страницу результатов,
                    # проверяем, что мы действительно на следующей странице
                    if str(page + 1) not in driver.current_url and "p=" + str(page + 1) not in driver.current_url:
                        print(
                            f"Возможно, переход на страницу {page + 1} не произошел. Текущий URL: {driver.current_url}")
                        # Пытаемся еще раз перейти на следующую страницу
                        driver.get(f"https://yandex.ru/search/?text={quote_plus(query)}&p={page}")
                        time.sleep(2)
                        # Еще раз проверяем капчу
                        check_and_solve_captcha(driver)

                # Ждем загрузки новых результатов
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "li.serp-item"))
                    )
                except TimeoutException:
                    # Проверяем альтернативные селекторы и URL
                    if "search" in driver.current_url and (
                            f"p={page}" in driver.current_url or f"p={page + 1}" in driver.current_url):
                        print("Мы на странице результатов, но не нашли стандартный селектор. Продолжаем...")
                    else:
                        print(f"Не удалось подтвердить переход на страницу {page + 1}. Проверьте браузер.")
                        input("Нажмите Enter для продолжения после проверки...")

            except (TimeoutException, NoSuchElementException) as e:
                print(f"Не удалось перейти на страницу {page + 1}: {str(e)}")
                break

    # Проверяем страницы результатов поиска
    for page in range(num_pages):
        if page > 0:
            print(f"Переход на страницу {page + 1} результатов...")
            try:
                # Находим кнопку перехода на следующую страницу
                next_page = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, f"a[aria-label='Страница {page + 1}']"))
                )

                # Прокручиваем страницу вниз для лучшей видимости кнопки
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_page)
                time.sleep(random.uniform(0.5, 1.5))

                # Кликаем на кнопку следующей страницы
                next_page.click()

                # Ждем загрузки новых результатов
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "li.serp-item"))
                )

            except (TimeoutException, NoSuchElementException) as e:
                print(f"Не удалось перейти на страницу {page + 1}: {str(e)}")
                break

        # Делаем небольшую паузу для загрузки и имитации поведения пользователя
        time.sleep(random.uniform(1, 3))
        print(f"Анализ результатов на странице {page + 1}...")

        # Прокручиваем страницу вниз медленно, имитируя чтение результатов
        driver.execute_script("window.scrollTo(0, 0);")  # Начинаем с верха страницы
        for scroll_position in range(0, 3000, 100):
            driver.execute_script(f"window.scrollTo(0, {scroll_position});")
            time.sleep(random.uniform(0.1, 0.3))

        # Собираем все результаты поиска на текущей странице
        search_results = driver.find_elements(By.CSS_SELECTOR, "li.serp-item")

        # Анализируем каждый результат поиска
        for result in search_results:
            position += 1
            try:
                # Находим заголовок и ссылку
                link_element = result.find_element(By.CSS_SELECTOR, "a.Link")
                title = link_element.text.strip()
                url = link_element.get_attribute("href")

                print(f"  [{position}] {title} - {url}")

                # Проверяем, содержится ли целевой домен в URL
                if target_domain in url:
                    print(
                        f"\nНАЙДЕНО! Сайт с доменом '{target_domain}' найден на позиции {position}, страница {page + 1}")

                    # Выделяем найденный результат
                    driver.execute_script("arguments[0].style.border='3px solid red';", result)
                    time.sleep(1)

                    # Прокручиваем страницу к найденному результату
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", result)
                    time.sleep(2)

                    return {
                        "position": position,
                        "url": url,
                        "title": title,
                        "page": page + 1,
                        "element": result
                    }

                results.append({
                    "position": position,
                    "url": url,
                    "title": title
                })

            except (NoSuchElementException, Exception) as e:
                print(f"  Ошибка при анализе результата {position}: {str(e)}")

    print(f"\nСайт с доменом '{target_domain}' не найден в первых {num_pages} страницах результатов поиска.")
    return None


def click_search_result(driver, result_element):
    """
    Имитирует переход по ссылке из поисковой выдачи

    Args:
        driver (webdriver): Экземпляр браузера
        result_element: Элемент с результатом поиска
    """
    try:
        # Находим ссылку в найденном результате
        link_element = result_element.find_element(By.CSS_SELECTOR, "a.Link")

        # Прокручиваем страницу к элементу, чтобы он был видим
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", link_element)
        time.sleep(1)

        print("Переход по найденной ссылке...")
        link_element.click()

        # Ждем загрузки страницы
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
        except TimeoutException:
            print("Превышено время ожидания загрузки страницы")

        # Выводим информацию о загруженной странице
        print(f"Страница загружена: {driver.current_url}")
        print(f"Заголовок страницы: {driver.title}")

        # Прокручиваем страницу, имитируя чтение
        total_height = driver.execute_script("return document.body.scrollHeight")
        for scroll_position in range(0, total_height, 200):
            driver.execute_script(f"window.scrollTo(0, {scroll_position});")
            time.sleep(random.uniform(0.2, 0.5))

        return True
    except Exception as e:
        print(f"Ошибка при переходе по ссылке: {str(e)}")
        return False


def find_and_copy_phone_number(driver, min_time_seconds=15):
    """
    Находит номер телефона на странице, выделяет его и копирует в буфер обмена

    Args:
        driver (webdriver): Экземпляр браузера
        min_time_seconds (int): Минимальное время пребывания на странице в секундах

    Returns:
        str: Найденный номер телефона или None
    """
    print(f"\nПросматриваем страницу минимум {min_time_seconds} секунд и ищем телефонный номер...")

    # Засекаем время начала
    start_time = time.time()

    # Прокручиваем страницу, чтобы имитировать чтение контента
    total_height = driver.execute_script("return document.body.scrollHeight")
    scroll_step = min(200, total_height // 10)

    # Медленная прокрутка вниз
    for scroll_position in range(0, total_height, scroll_step):
        driver.execute_script(f"window.scrollTo(0, {scroll_position});")
        time.sleep(random.uniform(0.3, 0.8))

    # Медленная прокрутка вверх
    for scroll_position in range(total_height, 0, -scroll_step):
        driver.execute_script(f"window.scrollTo(0, {scroll_position});")
        time.sleep(random.uniform(0.3, 0.8))

    # Пытаемся найти телефонный номер с помощью различных шаблонов
    phone_patterns = [
        # Регулярные выражения для поиска разных форматов телефонных номеров
        r'\+7\s*\(\d{3}\)\s*\d{3}[-\s]?\d{2}[-\s]?\d{2}',  # +7 (123) 456-78-90
        r'8\s*\(\d{3}\)\s*\d{3}[-\s]?\d{2}[-\s]?\d{2}',  # 8 (123) 456-78-90
        r'\+7\s*\d{3}\s*\d{3}\s*\d{2}\s*\d{2}',  # +7 123 456 78 90
        r'8\s*\d{3}\s*\d{3}\s*\d{2}\s*\d{2}',  # 8 123 456 78 90
        r'\d{1}[-\s]?\d{3}[-\s]?\d{3}[-\s]?\d{2}[-\s]?\d{2}',  # 8-123-456-78-90
        r'\+\d{1,4}[-\s]?\d{3}[-\s]?\d{3}[-\s]?\d{4}'  # +7-123-456-7890
    ]

    # Получаем текст страницы
    page_text = driver.find_element(By.TAG_NAME, "body").text

    # Попробуем найти телефон в тексте страницы
    phone_number = None
    for pattern in phone_patterns:
        import re
        matches = re.findall(pattern, page_text)
        if matches:
            phone_number = matches[0]
            print(f"Найден номер телефона в тексте: {phone_number}")
            break

    # Если телефон не найден в тексте, поищем элементы с атрибутами href="tel:"
    if not phone_number:
        try:
            tel_links = driver.find_elements(By.XPATH, "//a[contains(@href, 'tel:')]")
            if tel_links:
                for tel_link in tel_links:
                    href = tel_link.get_attribute("href")
                    if href and href.startswith("tel:"):
                        phone_number = href.replace("tel:", "")
                        print(f"Найден номер телефона в ссылке tel: {phone_number}")
                        break
        except Exception as e:
            print(f"Ошибка при поиске ссылок tel: {str(e)}")

    # Если телефон все еще не найден, поищем элементы с классами или id, содержащими слово phone/telefon/tel
    if not phone_number:
        try:
            phone_elements = driver.find_elements(By.XPATH,
                                                  "//*[contains(@class, 'phone') or contains(@class, 'tel') or contains(@id, 'phone') or contains(@id, 'tel')]")
            if phone_elements:
                for elem in phone_elements:
                    elem_text = elem.text.strip()
                    if elem_text:
                        for pattern in phone_patterns:
                            import re
                            matches = re.findall(pattern, elem_text)
                            if matches:
                                phone_number = matches[0]
                                print(f"Найден номер телефона в элементе с классом/id: {phone_number}")
                                break
                        if phone_number:
                            break
        except Exception as e:
            print(f"Ошибка при поиске элементов с классами phone/tel: {str(e)}")

    # Проверяем, прошло ли минимальное время пребывания на странице
    elapsed_time = time.time() - start_time
    remaining_time = min_time_seconds - elapsed_time

    if remaining_time > 0:
        print(f"Продолжаем осмотр страницы еще {remaining_time:.1f} секунд...")
        time.sleep(remaining_time)

    # Если телефон найден, выделяем его и копируем в буфер обмена
    if phone_number:
        try:
            print(f"Выделяем и копируем найденный номер телефона: {phone_number}")

            # Создаем временное текстовое поле для копирования
            driver.execute_script("""
                const tempInput = document.createElement('input');
                tempInput.value = arguments[0];
                document.body.appendChild(tempInput);
                tempInput.select();
                document.execCommand('copy');
                document.body.removeChild(tempInput);
                return true;
            """, phone_number)

            print("Номер телефона успешно скопирован в буфер обмена!")

            # Имитируем щелчок на элементе с телефоном для большей реалистичности
            try:
                if phone_elements and len(phone_elements) > 0:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", phone_elements[0])
                    time.sleep(0.5)

                    # Подсветим этот элемент
                    driver.execute_script("arguments[0].style.border='3px solid green';", phone_elements[0])
                    time.sleep(1)

                    try:
                        phone_elements[0].click()
                        time.sleep(0.5)
                    except:
                        # Если клик не сработал, просто продолжаем
                        pass
            except Exception as e:
                print(f"Ошибка при взаимодействии с элементом телефона: {str(e)}")

        except Exception as e:
            print(f"Ошибка при копировании номера телефона: {str(e)}")
    else:
        print("Номер телефона не найден на странице.")

    return phone_number


def get_user_input():
    """
    Запрашивает у пользователя параметры для поиска,
    если они не были переданы через командную строку

    Returns:
        tuple: (query, domain, pages, headless)
    """
    print("=" * 50)
    print("ПОИСК САЙТА В ВЫДАЧЕ ЯНДЕКСА")
    print("=" * 50)

    query = input("Введите поисковый запрос: ")
    while not query.strip():
        query = input("Поисковый запрос не может быть пустым. Введите запрос: ")

    domain = input("Введите домен для поиска (например, example.com): ")
    while not domain.strip():
        domain = input("Домен не может быть пустым. Введите домен: ")

    pages_input = input("Введите количество страниц для проверки [3]: ")
    pages = 3  # Значение по умолчанию

    if pages_input.strip():
        try:
            pages = int(pages_input)
            if pages <= 0:
                print("Количество страниц должно быть положительным. Будет использовано значение 3.")
                pages = 3
        except ValueError:
            print("Некорректное значение. Будет использовано значение 3.")

    headless_input = input("Запустить браузер в видимом режиме? (y/n) [y]: ").lower().strip()
    headless = False if headless_input == "" or headless_input in ["y", "yes", "д", "да"] else True

    return query, domain, pages, headless


def main():
    parser = argparse.ArgumentParser(description='Поиск сайта в поисковой выдаче Яндекса с визуализацией')
    parser.add_argument('--query', type=str, help='Поисковый запрос')
    parser.add_argument('--domain', type=str, help='Домен для поиска')
    parser.add_argument('--pages', type=int, default=3, help='Количество страниц для проверки')
    parser.add_argument('--headless', action='store_true', help='Запустить браузер в фоновом режиме')
    parser.add_argument('--delay', type=float, default=1.0,
                        help='Множитель задержки между действиями (1.0 = нормальная скорость)')
    parser.add_argument('--stay-time', type=int, default=15, help='Минимальное время пребывания на сайте в секундах')

    args = parser.parse_args()

    # Если аргументы не переданы через командную строку, запрашиваем их у пользователя
    if not args.query or not args.domain:
        query, domain, pages, headless = get_user_input()
        delay_factor = 1.0
        stay_time = 15
    else:
        query = args.query
        domain = args.domain
        pages = args.pages
        headless = args.headless
        delay_factor = args.delay
        stay_time = args.stay_time

    # Настраиваем глобальные задержки
    global random
    original_uniform = random.uniform
    random.uniform = lambda a, b: original_uniform(a * delay_factor, b * delay_factor)

    print("\n" + "=" * 50)
    print(f"ПОИСК САЙТА В ВЫДАЧЕ ЯНДЕКСА")
    print("=" * 50)
    print(f"Поисковый запрос: '{query}'")
    print(f"Искомый домен: '{domain}'")
    print(f"Количество страниц: {pages}")
    print(f"Режим работы: {'Фоновый' if headless else 'Видимый'}")
    print(f"Фактор задержки: {delay_factor}x")
    print(f"Время на сайте: {stay_time} сек.")
    print("-" * 50)

    # Инициализируем браузер
    driver = setup_browser(headless)

    try:
        # Выполняем поиск
        result = search_yandex(driver, query, domain, pages)

        if result:
            print("\n" + "=" * 50)
            print("РЕЗУЛЬТАТ ПОИСКА:")
            print(f"Сайт найден на позиции {result['position']} на странице {result['page']}")
            print(f"URL: {result['url']}")
            print(f"Заголовок: {result['title']}")
            print("=" * 50)

            should_click = input("\nПерейти по найденной ссылке? (y/n) [y]: ").lower().strip()
            if should_click == "" or should_click in ["y", "yes", "д", "да"]:
                # Переходим по ссылке
                if click_search_result(driver, result["element"]):
                    # Ищем и копируем номер телефона
                    phone_number = find_and_copy_phone_number(driver, stay_time)

                    if phone_number:
                        print(f"\nНайденный и скопированный номер телефона: {phone_number}")

                        # Сохраняем номер телефона в файл
                        with open("phone_numbers.txt", "a", encoding="utf-8") as f:
                            f.write(f"{domain}: {phone_number} ({time.strftime('%Y-%m-%d %H:%M:%S')})\n")
                        print("Номер телефона сохранен в файл phone_numbers.txt")

                    # Предложим сделать скриншот страницы
                    should_screenshot = input("\nСделать скриншот страницы? (y/n) [y]: ").lower().strip()
                    if should_screenshot == "" or should_screenshot in ["y", "yes", "д", "да"]:
                        screenshot_file = f"screenshot_{int(time.time())}.png"
                        driver.save_screenshot(screenshot_file)
                        print(f"Скриншот сохранен в файл: {screenshot_file}")

                # Дополнительная пауза перед закрытием браузера, чтобы пользователь мог осмотреть страницу
                wait_time = input("\nНажмите Enter для закрытия браузера... ")
        else:
            input("\nНажмите Enter для закрытия браузера... ")

    except Exception as e:
        print(f"\nПроизошла ошибка: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        # Закрываем браузер
        print("\nЗакрытие браузера...")
        try:
            driver.quit()
        except Exception as e:
            print(f"Ошибка при закрытии браузера: {str(e)}")
        print("Работа программы завершена.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nПрограмма прервана пользователем.")
    except Exception as e:
        print(f"\nПроизошла непредвиденная ошибка: {str(e)}")