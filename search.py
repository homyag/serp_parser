import time
import random
from urllib.parse import quote_plus
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Импортируем другие модули проекта
from captcha_solver import check_and_solve_captcha
from browser_utils import scroll_page
from config import (
    YANDEX_BASE_URL,
    YANDEX_SEARCH_URL,
    SEARCH_RESULT_SELECTORS,
    LINK_SELECTORS,
    NEXT_PAGE_SELECTORS
)


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
    driver.get(YANDEX_BASE_URL)
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

    # Анализируем страницы результатов поиска
    result = analyze_search_pages(driver, query, target_domain, num_pages)
    return result


def analyze_search_pages(driver, query, target_domain, num_pages=3):
    """
    Анализирует страницы результатов поиска и ищет целевой домен

    Args:
        driver (webdriver): Экземпляр браузера
        query (str): Поисковый запрос (для формирования URL)
        target_domain (str): Домен, который нужно найти
        num_pages (int): Количество страниц поиска для проверки

    Returns:
        dict: Информация о найденном результате или None
    """
    position = 0
    results = []

    for page in range(num_pages):
        # Делаем небольшую паузу для загрузки и имитации поведения пользователя
        time.sleep(random.uniform(1, 3))
        print(f"Анализ результатов на странице {page + 1}...")

        # Прокручиваем страницу вниз медленно, имитируя чтение результатов
        scroll_page(driver, "down", 100, 3000)

        # Собираем все результаты поиска на текущей странице
        search_results = []
        for selector in SEARCH_RESULT_SELECTORS:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements and len(elements) > 0:
                    search_results = elements
                    print(f"Найдено {len(elements)} результатов поиска по селектору: {selector}")
                    break
            except:
                continue

        if not search_results:
            print("Не удалось найти результаты поиска на странице.")
            # Проверяем наличие капчи, возможно она появилась
            if check_and_solve_captcha(driver):
                # Пробуем снова найти результаты после решения капчи
                for selector in SEARCH_RESULT_SELECTORS:
                    try:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        if elements and len(elements) > 0:
                            search_results = elements
                            print(f"После решения капчи найдено {len(elements)} результатов по селектору: {selector}")
                            break
                    except:
                        continue

            if not search_results:
                print(f"Пропускаем страницу {page + 1}, результаты не найдены.")
                continue

        # Анализируем каждый результат поиска
        found_result = analyze_search_results(driver, search_results, target_domain, position, page + 1)
        if found_result:
            return found_result

        # Обновляем позицию для следующей страницы
        position += len(search_results)

        # Если нужно просмотреть еще страницы
        if page < num_pages - 1:
            if not go_to_next_page(driver, query, page):
                break

    print(f"\nСайт с доменом '{target_domain}' не найден в первых {num_pages} страницах результатов поиска.")
    return None


def analyze_search_results(driver, search_results, target_domain, start_position, page_num):
    """
    Анализирует результаты поиска на текущей странице

    Args:
        driver (webdriver): Экземпляр браузера
        search_results (list): Список элементов с результатами поиска
        target_domain (str): Домен, который нужно найти
        start_position (int): Начальная позиция для нумерации результатов
        page_num (int): Номер текущей страницы

    Returns:
        dict: Информация о найденном результате или None
    """
    position = start_position
    results = []

    for result in search_results:
        position += 1
        try:
            # Находим заголовок и ссылку
            link_element = None

            for selector in LINK_SELECTORS:
                try:
                    links = result.find_elements(By.CSS_SELECTOR, selector)
                    if links and len(links) > 0:
                        link_element = links[0]
                        break
                except:
                    continue

            if not link_element:
                print(f"  [{position}] Не удалось найти ссылку в результате")
                continue

            title = link_element.text.strip()
            url = link_element.get_attribute("href")

            if not url or not title:
                # Если не удалось получить URL или заголовок стандартным способом, пробуем другие методы
                if not title:
                    try:
                        title_elements = result.find_elements(By.CSS_SELECTOR,
                                                              "h2, .organic__title, .OrganicTitle-Title")
                        if title_elements:
                            title = title_elements[0].text.strip()
                    except:
                        pass

                if not url:
                    try:
                        url = link_element.get_attribute("data-url") or link_element.get_attribute("data-href")
                    except:
                        pass

            if not url:
                print(f"  [{position}] Не удалось получить URL для результата")
                continue

            if not title:
                title = "Без заголовка"

            print(f"  [{position}] {title} - {url}")

            # Проверяем, содержится ли целевой домен в URL
            if target_domain in url:
                print(f"\nНАЙДЕНО! Сайт с доменом '{target_domain}' найден на позиции {position}, страница {page_num}")

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
                    "page": page_num,
                    "element": result
                }

            results.append({
                "position": position,
                "url": url,
                "title": title
            })

        except (NoSuchElementException, Exception) as e:
            print(f"  Ошибка при анализе результата {position}: {str(e)}")

    return None  # Не найдено на этой странице


def go_to_next_page(driver, query, current_page):
    """
    Переходит на следующую страницу результатов поиска

    Args:
        driver (webdriver): Экземпляр браузера
        query (str): Поисковый запрос (для формирования URL)
        current_page (int): Текущая страница (0-based)

    Returns:
        bool: True, если успешно перешли на следующую страницу, False в противном случае
    """
    next_page_num = current_page + 2  # +2 потому что current_page 0-based, а номера страниц 1-based
    print(f"Переход на страницу {next_page_num} результатов...")

    try:
        # Находим кнопку перехода на следующую страницу
        next_page = None
        for selector in NEXT_PAGE_SELECTORS:
            try:
                # Заменяем {page} на номер страницы
                selector_with_page = selector.replace("{page}", str(next_page_num))

                if selector_with_page.startswith('//'):
                    elements = driver.find_elements(By.XPATH, selector_with_page)
                else:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector_with_page)

                if elements and len(elements) > 0:
                    next_page = elements[0]
                    print(f"Найдена кнопка следующей страницы по селектору: {selector}")
                    break
            except:
                continue

        if not next_page:
            print("Не удалось найти кнопку перехода на следующую страницу.")
            # Пробуем прямой переход по URL
            next_page_url = f"{YANDEX_SEARCH_URL}?text={quote_plus(query)}&p={current_page + 1}"
            print(f"Пробуем прямой переход по URL: {next_page_url}")
            driver.get(next_page_url)
            time.sleep(2)
            # Проверяем наличие капчи после прямого перехода
            check_and_solve_captcha(driver)
            return True

        # Прокручиваем страницу вниз для лучшей видимости кнопки
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_page)
        time.sleep(random.uniform(0.5, 1.5))

        # Кликаем на кнопку следующей страницы
        next_page.click()

        # Проверяем наличие капчи после клика на следующую страницу
        time.sleep(2)  # Даем время для загрузки страницы или капчи
        print("Проверяем наличие капчи после перехода на следующую страницу...")
        check_and_solve_captcha(driver)
        return True

    except (TimeoutException, NoSuchElementException, Exception) as e:
        print(f"Ошибка при переходе на следующую страницу: {str(e)}")
        # Пробуем прямой переход по URL
        next_page_url = f"{YANDEX_SEARCH_URL}?text={quote_plus(query)}&p={current_page + 1}"
        print(f"Пробуем прямой переход по URL после ошибки: {next_page_url}")
        driver.get(next_page_url)
        time.sleep(2)
        # Проверяем наличие капчи после прямого перехода
        check_and_solve_captcha(driver)
        return True