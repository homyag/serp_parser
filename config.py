# Конфигурационные параметры и константы для проекта

# Список User-Agent для имитации разных браузеров
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
]

# Селекторы для поиска капчи
CAPTCHA_SELECTORS = [
    "//div[contains(text(), 'Подтвердите, что запросы отправляете вы, а не робот')]",
    "//div[contains(@class, 'CheckboxCaptcha-Anchor')]",
    "//div[contains(@class, 'AdvancedCaptcha-Anchor')]",
    "//iframe[contains(@src, 'captcha')]",
    "//input[contains(@class, 'CheckboxCaptcha-Button')]",
    "//input[@id='js-button']",
    "//div[contains(text(), 'Вы робот?')]",
    "//div[contains(@class, 'Captcha')]"
]

# Селекторы для поиска чекбокса капчи
CHECKBOX_SELECTORS = [
    "//input[contains(@class, 'CheckboxCaptcha-Button')]",
    "//input[@id='js-button']",
    "//div[contains(@class, 'CheckboxCaptcha-Anchor')]",
    "//div[contains(@class, 'Checkbox-Anchor')]",
    "//div[@role='checkbox']",
    "//input[@role='checkbox']"
]

# Индикаторы успешного решения капчи
SUCCESS_INDICATORS = [
    "//li[contains(@class, 'serp-item')]",  # Результаты поиска
    "//div[contains(@class, 'CheckboxCaptcha-Success')]",  # Индикатор успеха
    "//div[contains(text(), 'Спасибо')]",  # Текст благодарности
]

# Селекторы для поиска результатов Яндекса
SEARCH_RESULT_SELECTORS = [
    "li.serp-item",
    "div.serp-item",
    "div.organic",
    "div[data-fast-name='organic']",
    "div.OrganicTitle"
]

# Селекторы для ссылок в результатах поиска
LINK_SELECTORS = [
    "a.Link",
    "a.organic__url",
    "a.OrganicTitle-Link",
    "a"
]

# Селекторы для кнопок пагинации
NEXT_PAGE_SELECTORS = [
    "a[aria-label='Страница {page}']",
    "//a[contains(@aria-label, 'Страница {page}')]",
    "//a[contains(@class, 'Pager-Item_type_next')]",
    "//a[contains(@data-fast-name, 'next')]",
    "//div[contains(@class, 'pager')]//a[contains(text(), 'дальше')]",
    "//div[contains(@class, 'pager')]//a[contains(text(), 'следующая')]"
]

# Регулярные выражения для поиска телефонных номеров
PHONE_PATTERNS = [
    r'\+7\s*\(\d{3}\)\s*\d{3}[-\s]?\d{2}[-\s]?\d{2}',  # +7 (123) 456-78-90
    r'8\s*\(\d{3}\)\s*\d{3}[-\s]?\d{2}[-\s]?\d{2}',    # 8 (123) 456-78-90
    r'\+7\s*\d{3}\s*\d{3}\s*\d{2}\s*\d{2}',           # +7 123 456 78 90
    r'8\s*\d{3}\s*\d{3}\s*\d{2}\s*\d{2}',             # 8 123 456 78 90
    r'\d{1}[-\s]?\d{3}[-\s]?\d{3}[-\s]?\d{2}[-\s]?\d{2}', # 8-123-456-78-90
    r'\+\d{1,4}[-\s]?\d{3}[-\s]?\d{3}[-\s]?\d{4}'      # +7-123-456-7890
]

# Базовый URL для Яндекса
YANDEX_BASE_URL = "https://ya.ru"
YANDEX_SEARCH_URL = f"{YANDEX_BASE_URL}/search/"

# Имя файла для сохранения номеров телефонов
PHONE_NUMBERS_FILE = "phone_numbers.txt"

# Префикс для скриншотов
SCREENSHOT_PREFIX = "screenshot_"

# Параметры по умолчанию
DEFAULT_PAGES = 3
DEFAULT_STAY_TIME = 15
DEFAULT_DELAY_FACTOR = 1.0