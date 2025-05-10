"""
Скрипт для поиска сайта в выдаче Яндекса и глубокого взаимодействия с найденным сайтом.

Автоматически находит заданный домен в выдаче поиска Яндекса по указанному запросу,
переходит на него, взаимодействует с элементами страницы, заполняет формы и находит телефонные номера.
"""

import argparse
import random
import time
import traceback

# Импортируем модули проекта
from config import DEFAULT_PAGES, DEFAULT_STAY_TIME, DEFAULT_DELAY_FACTOR, SCREENSHOT_PREFIX
from browser_utils import setup_browser, safe_close_browser, make_screenshot
from search import search_yandex
from content_extractor import click_search_result, find_and_copy_phone_number, save_phone_to_file
from site_interaction import interact_with_site, is_yandex_url  # Новый модуль для взаимодействия с сайтом
from user_interface import (
    get_user_input,
    ask_user_yes_no,
    display_search_result,
    display_found_phone,
    wait_for_user_interaction,
    display_screenshot_path,
    show_program_start_info,
    show_error_message,
    show_program_end,
    get_interaction_level  # Функция для выбора уровня взаимодействия
)


def parse_arguments():
    """Парсинг аргументов командной строки"""
    parser = argparse.ArgumentParser(description='Поиск сайта в поисковой выдаче Яндекса с визуализацией')
    parser.add_argument('--query', type=str, help='Поисковый запрос')
    parser.add_argument('--domain', type=str, help='Домен для поиска')
    parser.add_argument('--pages', type=int, default=DEFAULT_PAGES, help='Количество страниц для проверки')
    parser.add_argument('--headless', action='store_true', help='Запустить браузер в фоновом режиме')
    parser.add_argument('--delay', type=float, default=DEFAULT_DELAY_FACTOR,
                        help='Множитель задержки между действиями (1.0 = нормальная скорость)')
    parser.add_argument('--stay-time', type=int, default=DEFAULT_STAY_TIME,
                        help='Минимальное время пребывания на сайте в секундах')
    parser.add_argument('--interaction', type=str, choices=['low', 'medium', 'high'], default='medium',
                        help='Уровень взаимодействия с сайтом (low, medium, high)')

    return parser.parse_args()


def main():
    """Основная функция программы"""
    # Парсим аргументы командной строки
    args = parse_arguments()

    # Если аргументы не переданы через командную строку, запрашиваем их у пользователя
    if not args.query or not args.domain:
        query, domain, pages, headless = get_user_input()
        delay_factor = DEFAULT_DELAY_FACTOR
        stay_time = DEFAULT_STAY_TIME
        # Запрашиваем уровень взаимодействия отдельно
        interaction_level = get_interaction_level()
    else:
        query = args.query
        domain = args.domain
        pages = args.pages
        headless = args.headless
        delay_factor = args.delay
        stay_time = args.stay_time
        interaction_level = args.interaction

    # Настраиваем глобальные задержки
    global random
    original_uniform = random.uniform
    random.uniform = lambda a, b: original_uniform(a * delay_factor, b * delay_factor)

    # Отображаем информацию о параметрах запуска
    show_program_start_info(query, domain, pages, headless, delay_factor, stay_time, interaction_level)

    # Инициализируем браузер
    driver = setup_browser(headless)

    try:
        # Выполняем поиск
        result = search_yandex(driver, query, domain, pages)

        if result:
            # Отображаем результат поиска
            display_search_result(result)

            # Спрашиваем, переходить ли по найденной ссылке
            if ask_user_yes_no("Перейти по найденной ссылке?"):
                # Переходим по ссылке
                if click_search_result(driver, result["element"]):
                    # Сохраняем текущий URL после перехода
                    target_site_url = driver.current_url

                    # Проверяем, что мы действительно перешли на целевой сайт, а не остались на Яндексе
                    if is_yandex_url(driver.current_url):
                        print("\nВНИМАНИЕ: После клика мы все еще находимся на странице Яндекса.")
                        print("Проверяем, открылся ли сайт в новом окне...")

                        # Проверяем, есть ли другие открытые окна
                        if len(driver.window_handles) > 1:
                            print(
                                f"Обнаружено {len(driver.window_handles)} открытых окон. Пытаемся найти целевой сайт.")

                            # Запоминаем текущее окно
                            current_window = driver.current_window_handle
                            target_window = None

                            # Проверяем все окна, ищем целевой сайт
                            for window_handle in driver.window_handles:
                                if window_handle != current_window:
                                    driver.switch_to.window(window_handle)
                                    print(f"Проверяем окно: {driver.current_url}")

                                    # Если URL содержит домен, который мы ищем
                                    if domain in driver.current_url or not is_yandex_url(driver.current_url):
                                        print(f"Найден целевой сайт в другом окне: {driver.current_url}")
                                        target_window = window_handle
                                        target_site_url = driver.current_url
                                        break

                            # Если не нашли целевое окно, возвращаемся к исходному
                            if not target_window:
                                print("Целевой сайт не найден в открытых окнах. Возвращаемся к Яндексу.")
                                driver.switch_to.window(current_window)
                                wait_for_user_interaction()
                                return
                        else:
                            print("Не найдено дополнительных окон. Продолжаем работу в текущем окне.")

                    # Сначала ищем телефон (это делается без активного взаимодействия с элементами)
                    phone_number = find_and_copy_phone_number(driver, 5)  # Уменьшаем время первичного поиска

                    if phone_number:
                        save_phone_to_file(domain, phone_number)
                        display_found_phone(phone_number, domain)
                    else:
                        print("\nНа начальной странице телефон не найден. Будет выполнено активное взаимодействие с сайтом.")

                    # Запоминаем текущий URL для проверки
                    target_site_url = driver.current_url

                    # Предлагаем активно взаимодействовать с сайтом
                    if ask_user_yes_no("Выполнить активное взаимодействие с сайтом (клики, формы, переходы)?"):
                        # Проверяем еще раз, что мы находимся на целевом сайте
                        if is_yandex_url(driver.current_url):
                            print("\nОШИБКА: В данный момент мы находимся на странице Яндекса")
                            print("Переходим обратно на целевой сайт")
                            try:
                                driver.get(target_site_url)
                                time.sleep(3)
                            except:
                                print("Не удалось вернуться на целевой сайт")
                                wait_for_user_interaction()
                                return

                        # Активное взаимодействие с сайтом
                        interaction_results = interact_with_site(driver, stay_time, interaction_level)

                        # После взаимодействия пробуем еще раз найти телефон, если он не был найден ранее
                        if not phone_number:
                            print("\nПопытка найти телефон после взаимодействия с сайтом...")
                            phone_number = find_and_copy_phone_number(driver, 5)

                            if phone_number:
                                save_phone_to_file(domain, phone_number)
                                display_found_phone(phone_number, domain)
                            else:
                                print("Телефон не найден и после активного взаимодействия с сайтом.")

                        # Отображаем информацию о взаимодействии
                        print(f"\nВыполнено {interaction_results['clicked_elements']} кликов на элементы")
                        print(f"Заполнено {interaction_results['filled_forms']} форм")
                        print(f"Посещено {len(interaction_results['visited_pages'])} страниц")

                        # Выводим список страниц, которые мы посетили
                        if len(interaction_results['visited_pages']) > 1:
                            print("\nПосещенные страницы:")
                            for i, page_url in enumerate(interaction_results['visited_pages']):
                                print(f"{i+1}. {page_url}")

                    # Предлагаем сделать скриншот текущей страницы
                    if ask_user_yes_no("Сделать скриншот текущей страницы?"):
                        screenshot_file = make_screenshot(driver, SCREENSHOT_PREFIX)
                        display_screenshot_path(screenshot_file)

                # Ожидаем действия пользователя перед закрытием браузера
                wait_for_user_interaction()
        else:
            # Если сайт не найден, ожидаем действия пользователя
            wait_for_user_interaction()

    except Exception as e:
        # Отображаем информацию об ошибке
        show_error_message(e)

    finally:
        # Закрываем браузер
        safe_close_browser(driver)
        show_program_end()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nПрограмма прервана пользователем.")
    except Exception as e:
        print(f"\nПроизошла непредвиденная ошибка: {str(e)}")
        traceback.print_exc()