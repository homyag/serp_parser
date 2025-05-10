import random
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Импортируем константы из config
from config import USER_AGENTS, YANDEX_BASE_URL


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


def scroll_page(driver, direction="down", step=100, max_scroll=3000, random_delay=True):
    """
    Прокручивает страницу имитируя чтение пользователем

    Args:
        driver (webdriver): Экземпляр браузера
        direction (str): Направление прокрутки ("down" или "up")
        step (int): Шаг прокрутки в пикселях
        max_scroll (int): Максимальное расстояние прокрутки
        random_delay (bool): Использовать ли случайные задержки
    """
    if direction == "down":
        # Начинаем с верха страницы
        driver.execute_script("window.scrollTo(0, 0);")

        # Медленная прокрутка вниз
        for scroll_position in range(0, max_scroll, step):
            driver.execute_script(f"window.scrollTo(0, {scroll_position});")
            if random_delay:
                time.sleep(random.uniform(0.1, 0.3))
            else:
                time.sleep(0.1)
    else:  # direction == "up"
        # Медленная прокрутка вверх
        total_height = driver.execute_script("return document.body.scrollHeight")
        for scroll_position in range(total_height, 0, -step):
            driver.execute_script(f"window.scrollTo(0, {scroll_position});")
            if random_delay:
                time.sleep(random.uniform(0.1, 0.3))
            else:
                time.sleep(0.1)


def make_screenshot(driver, prefix="screenshot_"):
    """
    Делает скриншот страницы

    Args:
        driver (webdriver): Экземпляр браузера
        prefix (str): Префикс имени файла скриншота

    Returns:
        str: Имя созданного файла скриншота
    """
    screenshot_file = f"{prefix}{int(time.time())}.png"
    driver.save_screenshot(screenshot_file)
    return screenshot_file


def safe_close_browser(driver):
    """
    Безопасно закрывает браузер

    Args:
        driver (webdriver): Экземпляр браузера
    """
    try:
        print("Закрытие браузера...")
        driver.quit()
    except Exception as e:
        print(f"Ошибка при закрытии браузера: {str(e)}")