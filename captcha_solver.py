import time
import random
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

# Импортируем константы из конфига
from config import CAPTCHA_SELECTORS, CHECKBOX_SELECTORS, SUCCESS_INDICATORS


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
        for selector in CHECKBOX_SELECTORS:
            try:
                checkbox = driver.find_element(By.XPATH, selector)
                if checkbox.is_displayed():
                    print(f"Найден чекбокс: {selector}")

                    # Имитируем человеческое поведение перед кликом
                    # Сначала наведем мышь немного рядом с чекбоксом
                    action = ActionChains(driver)

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
                        for indicator in SUCCESS_INDICATORS:
                            if len(driver.find_elements(By.XPATH, indicator)) > 0:
                                print("Капча успешно решена автоматически!")
                                return True

                        # Если индикаторы не найдены, попробуем вариант 2: JavaScript клик
                        print("Первый способ не сработал, пробуем JavaScript клик...")
                        driver.execute_script("arguments[0].click();", checkbox)
                        time.sleep(random.uniform(1.0, 2.0))

                        # Снова проверяем успех
                        for indicator in SUCCESS_INDICATORS:
                            if len(driver.find_elements(By.XPATH, indicator)) > 0:
                                print("Капча успешно решена автоматически (JavaScript клик)!")
                                return True

                        # Если это тоже не сработало, используем дополнительные методы
                        print("JavaScript клик не сработал, пробуем Space и Enter...")

                        # Вариант 3: Фокус + Space или Enter
                        checkbox.send_keys(Keys.SPACE)
                        time.sleep(random.uniform(0.5, 1.0))

                        # Снова проверяем успех
                        for indicator in SUCCESS_INDICATORS:
                            if len(driver.find_elements(By.XPATH, indicator)) > 0:
                                print("Капча успешно решена автоматически (Space)!")
                                return True

                        # Последняя попытка с Enter
                        checkbox.send_keys(Keys.ENTER)
                        time.sleep(random.uniform(0.5, 1.0))

                        # Финальная проверка
                        for indicator in SUCCESS_INDICATORS:
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


def check_and_solve_captcha(driver):
    """
    Проверяет наличие капчи и пытается её решить

    Args:
        driver (webdriver): Экземпляр браузера

    Returns:
        bool: True, если капчи не было или она была успешно решена, False если не удалось решить
    """
    captcha_found = False

    for selector in CAPTCHA_SELECTORS:
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