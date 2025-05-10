#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для поиска сайта в выдаче Яндекса и сбора информации с найденного сайта.

Автоматически находит заданный домен в выдаче поиска Яндекса по указанному запросу,
переходит на него, находит и копирует номер телефона.
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
from user_interface import (
    get_user_input,
    ask_user_yes_no,
    display_search_result,
    display_found_phone,
    wait_for_user_interaction,
    display_screenshot_path,
    show_program_start_info,
    show_error_message,
    show_program_end
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

    # Отображаем информацию о параметрах запуска
    show_program_start_info(query, domain, pages, headless, delay_factor, stay_time)

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
                    # Ищем и копируем номер телефона
                    phone_number = find_and_copy_phone_number(driver, stay_time)

                    if phone_number:
                        # Сохраняем номер телефона в файл и отображаем его
                        save_phone_to_file(domain, phone_number)
                        display_found_phone(phone_number, domain)

                    # Предлагаем сделать скриншот страницы
                    if ask_user_yes_no("Сделать скриншот страницы?"):
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