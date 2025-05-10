import re
import time
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

# Импортируем из других модулей
from browser_utils import scroll_page
from config import PHONE_PATTERNS


def click_search_result(driver, result_element):
    """
    Имитирует переход по ссылке из поисковой выдачи

    Args:
        driver (webdriver): Экземпляр браузера
        result_element: Элемент с результатом поиска

    Returns:
        bool: True, если переход успешен, False в противном случае
    """
    try:
        # Находим ссылку в найденном результате
        link_element = result_element.find_element(By.CSS_SELECTOR, "a.Link")

        # Прокручиваем страницу к элементу, чтобы он был видим
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", link_element)
        time.sleep(1)

        print("Переход по найденной ссылке...")
        link_element.click()

        # Ждем загрузки страницы (как минимум body должен появиться)
        try:
            driver.find_element(By.TAG_NAME, "body")
        except NoSuchElementException:
            print("Не удалось обнаружить загрузку страницы")
            return False

        # Выводим информацию о загруженной странице
        print(f"Страница загружена: {driver.current_url}")
        print(f"Заголовок страницы: {driver.title}")

        # Прокручиваем страницу, имитируя чтение
        total_height = driver.execute_script("return document.body.scrollHeight")
        for scroll_position in range(0, total_height, 200):
            driver.execute_script(f"window.scrollTo(0, {scroll_position});")
            time.sleep(0.3)

        return True
    except Exception as e:
        print(f"Ошибка при переходе по ссылке: {str(e)}")
        return False


def find_phone_numbers_in_text(text):
    """
    Ищет телефонные номера в тексте по регулярным выражениям

    Args:
        text (str): Текст для поиска

    Returns:
        list: Список найденных телефонных номеров
    """
    all_matches = []
    for pattern in PHONE_PATTERNS:
        matches = re.findall(pattern, text)
        if matches:
            all_matches.extend(matches)

    return all_matches


def find_tel_links(driver):
    """
    Ищет ссылки с префиксом tel: на странице

    Args:
        driver (webdriver): Экземпляр браузера

    Returns:
        list: Список телефонных номеров, извлеченных из ссылок tel:
    """
    phone_numbers = []
    try:
        tel_links = driver.find_elements(By.XPATH, "//a[contains(@href, 'tel:')]")
        for link in tel_links:
            href = link.get_attribute("href")
            if href and href.startswith("tel:"):
                phone_number = href.replace("tel:", "")
                phone_numbers.append(phone_number)
    except Exception as e:
        print(f"Ошибка при поиске ссылок tel: {str(e)}")

    return phone_numbers


def find_phone_elements(driver):
    """
    Ищет элементы, содержащие телефон, по классам или ID

    Args:
        driver (webdriver): Экземпляр браузера

    Returns:
        tuple: (Список номеров, Список элементов с телефонами)
    """
    phone_numbers = []
    phone_elements = []

    try:
        elements = driver.find_elements(By.XPATH,
                                        "//*[contains(@class, 'phone') or contains(@class, 'tel') or contains(@id, 'phone') or contains(@id, 'tel')]")

        for elem in elements:
            elem_text = elem.text.strip()
            if elem_text:
                matches = find_phone_numbers_in_text(elem_text)
                if matches:
                    phone_numbers.extend(matches)
                    phone_elements.append(elem)
    except Exception as e:
        print(f"Ошибка при поиске элементов с классами phone/tel: {str(e)}")

    return phone_numbers, phone_elements


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

    # Медленная прокрутка вниз и вверх
    scroll_page(driver, "down", scroll_step, total_height)
    scroll_page(driver, "up", scroll_step, total_height)

    # Получаем текст страницы
    page_text = driver.find_element(By.TAG_NAME, "body").text

    # Ищем телефон в тексте страницы
    phone_number = None
    text_matches = find_phone_numbers_in_text(page_text)
    if text_matches:
        phone_number = text_matches[0]
        print(f"Найден номер телефона в тексте: {phone_number}")

    # Если телефон не найден в тексте, ищем ссылки tel:
    if not phone_number:
        tel_links = find_tel_links(driver)
        if tel_links:
            phone_number = tel_links[0]
            print(f"Найден номер телефона в ссылке tel: {phone_number}")

    # Если телефон все еще не найден, ищем элементы с классами или ID phone/tel
    phone_elements = None
    if not phone_number:
        numbers, elements = find_phone_elements(driver)
        if numbers:
            phone_number = numbers[0]
            phone_elements = elements
            print(f"Найден номер телефона в элементе с классом/id: {phone_number}")

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
            if phone_elements and len(phone_elements) > 0:
                try:
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


def save_phone_to_file(domain, phone_number, filename="phone_numbers.txt"):
    """
    Сохраняет найденный номер телефона в файл

    Args:
        domain (str): Домен сайта
        phone_number (str): Номер телефона
        filename (str): Имя файла для сохранения

    Returns:
        bool: True, если сохранение успешно, False в противном случае
    """
    try:
        with open(filename, "a", encoding="utf-8") as f:
            f.write(f"{domain}: {phone_number} ({time.strftime('%Y-%m-%d %H:%M:%S')})\n")
        return True
    except Exception as e:
        print(f"Ошибка при сохранении номера телефона в файл: {str(e)}")
        return False