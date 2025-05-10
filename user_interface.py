import time
from config import DEFAULT_PAGES, DEFAULT_STAY_TIME, PHONE_NUMBERS_FILE, SCREENSHOT_PREFIX


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

    pages_input = input(f"Введите количество страниц для проверки [{DEFAULT_PAGES}]: ")
    pages = DEFAULT_PAGES  # Значение по умолчанию

    if pages_input.strip():
        try:
            pages = int(pages_input)
            if pages <= 0:
                print(f"Количество страниц должно быть положительным. Будет использовано значение {DEFAULT_PAGES}.")
                pages = DEFAULT_PAGES
        except ValueError:
            print(f"Некорректное значение. Будет использовано значение {DEFAULT_PAGES}.")

    headless_input = input("Запустить браузер в видимом режиме? (y/n) [y]: ").lower().strip()
    headless = False if headless_input == "" or headless_input in ["y", "yes", "д", "да"] else True

    return query, domain, pages, headless


def get_interaction_level():
    """
    Запрашивает у пользователя уровень взаимодействия с сайтом

    Returns:
        str: Уровень взаимодействия ('low', 'medium', 'high')
    """
    print("\nВыберите уровень взаимодействия с сайтом:")
    print("1 - Низкий (минимальные действия)")
    print("2 - Средний (умеренное количество действий)")
    print("3 - Высокий (активное исследование сайта)")

    interaction_input = input("Введите номер [2]: ").strip()

    if not interaction_input or interaction_input == "2":
        return "medium"
    elif interaction_input == "1":
        return "low"
    elif interaction_input == "3":
        return "high"
    else:
        print("Некорректный ввод. Будет использован средний уровень взаимодействия.")
        return "medium"


def ask_user_yes_no(question, default=True):
    """
    Задает пользователю вопрос с вариантами ответа да/нет

    Args:
        question (str): Вопрос для пользователя
        default (bool): Значение по умолчанию (True = да, False = нет)

    Returns:
        bool: Ответ пользователя (True = да, False = нет)
    """
    default_str = "[y]" if default else "[n]"
    answer = input(f"{question} (y/n) {default_str}: ").lower().strip()

    if not answer:
        return default

    return answer in ["y", "yes", "д", "да"]


def display_search_result(result):
    """
    Отображает результат поиска

    Args:
        result (dict): Результат поиска
    """
    print("\n" + "=" * 50)
    print("РЕЗУЛЬТАТ ПОИСКА:")
    print(f"Сайт найден на позиции {result['position']} на странице {result['page']}")
    print(f"URL: {result['url']}")
    print(f"Заголовок: {result['title']}")
    print("=" * 50)


def display_found_phone(phone_number, domain):
    """
    Отображает найденный номер телефона

    Args:
        phone_number (str): Номер телефона
        domain (str): Домен сайта
    """
    if phone_number:
        print(f"\nНайденный и скопированный номер телефона: {phone_number}")
        print(f"Номер телефона сохранен в файл {PHONE_NUMBERS_FILE}")
    else:
        print(f"\nНа сайте {domain} не найден номер телефона.")


def wait_for_user_interaction():
    """
    Ожидает действия пользователя для продолжения
    """
    input("\nНажмите Enter для закрытия браузера... ")


def display_screenshot_path(screenshot_file):
    """
    Отображает путь к сохраненному скриншоту

    Args:
        screenshot_file (str): Имя файла скриншота
    """
    print(f"Скриншот сохранен в файл: {screenshot_file}")


def show_program_start_info(query, domain, pages, headless, delay_factor, stay_time, interaction_level="medium"):
    """
    Выводит информацию о параметрах запуска программы

    Args:
        query (str): Поисковый запрос
        domain (str): Домен для поиска
        pages (int): Количество страниц
        headless (bool): Запускать ли браузер в фоновом режиме
        delay_factor (float): Множитель задержки
        stay_time (int): Время пребывания на сайте
        interaction_level (str): Уровень взаимодействия с сайтом
    """
    print("\n" + "=" * 50)
    print(f"ПОИСК САЙТА В ВЫДАЧЕ ЯНДЕКСА")
    print("=" * 50)
    print(f"Поисковый запрос: '{query}'")
    print(f"Искомый домен: '{domain}'")
    print(f"Количество страниц: {pages}")
    print(f"Режим работы: {'Фоновый' if headless else 'Видимый'}")
    print(f"Фактор задержки: {delay_factor}x")
    print(f"Время на сайте: {stay_time} сек.")

    # Добавляем вывод уровня взаимодействия
    interaction_desc = {
        "low": "Низкий (минимальные действия)",
        "medium": "Средний (умеренное количество действий)",
        "high": "Высокий (активное исследование сайта)"
    }
    print(f"Уровень взаимодействия: {interaction_desc.get(interaction_level, 'Средний')}")

    print("-" * 50)


def show_error_message(error):
    """
    Отображает сообщение об ошибке

    Args:
        error (Exception): Объект исключения
    """
    print(f"\nПроизошла ошибка: {str(error)}")
    import traceback
    traceback.print_exc()


def show_program_end():
    """
    Отображает сообщение о завершении программы
    """
    print("Работа программы завершена.")