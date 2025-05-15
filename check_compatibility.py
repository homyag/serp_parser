import sys
import os
import importlib.util
import platform


def check_module(module_name):
    """Проверяет, установлен ли модуль"""
    spec = importlib.util.find_spec(module_name)
    if spec is None:
        return False
    return True


def main():
    """Проверяет совместимость и наличие зависимостей"""
    print("=" * 50)
    print("SERP Parser GUI - проверка совместимости")
    print("=" * 50)

    # Проверка версии Python
    py_version = sys.version_info
    print(f"Версия Python: {py_version.major}.{py_version.minor}.{py_version.micro}")
    if py_version.major < 3 or (py_version.major == 3 and py_version.minor < 6):
        print("ОШИБКА: Требуется Python 3.6 или выше")
        return False

    # Проверка операционной системы
    system = platform.system()
    print(f"Операционная система: {system}")

    # Проверка необходимых модулей
    required_modules = [
        "PyQt5", "selenium", "requests", "bs4", "webdriver_manager"
    ]

    all_modules_available = True
    for module in required_modules:
        if check_module(module):
            print(f"✓ Модуль {module} установлен")
        else:
            print(f"✗ Модуль {module} не установлен")
            all_modules_available = False

    if not all_modules_available:
        print("\nНе все необходимые модули установлены.")
        print("Установите их с помощью команды:")
        print("pip install -r requirements_updated.txt")
        return False

    # Проверка наличия необходимых файлов проекта
    project_files = [
        "ui_app.py", "run.py", "browser_utils.py", "search.py",
        "content_extractor.py", "site_interaction.py", "config.py"
    ]

    all_files_found = True
    for file in project_files:
        if os.path.exists(file):
            print(f"✓ Файл {file} найден")
        else:
            print(f"✗ Файл {file} не найден")
            all_files_found = False

    if not all_files_found:
        print("\nНе все необходимые файлы проекта найдены.")
        print("Убедитесь, что вы находитесь в корневой директории проекта и все файлы на месте.")
        return False

    print("\nПроверка совместимости завершена успешно!")
    print("Можно запускать приложение с помощью команды:")
    print("python run.py")
    return True


if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)