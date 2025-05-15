import sys
import os
import threading
import time
import logging
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
                             QPushButton, QTextEdit, QCheckBox, QTabWidget, QFileDialog,
                             QGroupBox, QFormLayout, QProgressBar, QMessageBox, QSplitter,
                             QSizePolicy)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QTimer, QSize
from PyQt5.QtGui import QIcon, QTextCursor, QPixmap


# Путь к ресурсам и изображениям
def resource_path(relative_path):
    """Получить абсолютный путь к ресурсу"""
    try:
        # PyInstaller создает временную папку и хранит путь в _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class LogRedirector:
    """Класс для перенаправления вывода логов в текстовое поле GUI"""

    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.buffer = ""
        # Настраиваем логгер
        self.logger = logging.getLogger('SERP_Parser')
        self.logger.setLevel(logging.INFO)

        # Обработчик для вывода в текстовое поле
        handler = logging.StreamHandler(self)
        formatter = logging.Formatter('%(asctime)s - %(message)s', '%H:%M:%S')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def write(self, text):
        """Запись текста в буфер и в виджет"""
        self.buffer += text
        if '\n' in self.buffer:
            lines = self.buffer.split('\n')
            self.buffer = lines[-1]
            for line in lines[:-1]:
                if line.strip():  # Пропускаем пустые строки
                    self.text_widget.append(line.rstrip())
                    # Прокрутка к последней строке
                    cursor = self.text_widget.textCursor()
                    cursor.movePosition(QTextCursor.End)
                    self.text_widget.setTextCursor(cursor)

    def flush(self):
        """Необходимый метод для работы со StreamHandler"""
        if self.buffer:
            self.text_widget.append(self.buffer.rstrip())
            self.buffer = ""


class SearchWorker(QThread):
    """Рабочий поток для выполнения поиска"""
    progressUpdated = pyqtSignal(int)
    statusUpdated = pyqtSignal(str)
    searchCompleted = pyqtSignal(dict)
    searchFailed = pyqtSignal(str)
    phoneFound = pyqtSignal(str)
    screenshotTaken = pyqtSignal(str)

    def __init__(self, params):
        super().__init__()
        self.params = params
        self.is_cancelled = False

    def run(self):
        """Выполнение поиска в отдельном потоке"""
        try:
            # Импортируем модули проекта здесь для изоляции от GUI
            from browser_utils import setup_browser, safe_close_browser, make_screenshot
            from search import search_yandex
            from content_extractor import click_search_result, find_and_copy_phone_number, save_phone_to_file
            from site_interaction import interact_with_site, is_yandex_url
            from config import PHONE_NUMBERS_FILE

            # Настраиваем глобальный фактор задержки
            import random
            original_uniform = random.uniform
            delay_factor = self.params['delay_factor']
            random.uniform = lambda a, b: original_uniform(a * delay_factor, b * delay_factor)

            self.statusUpdated.emit("Инициализация браузера...")
            self.progressUpdated.emit(10)

            # Инициализируем браузер
            driver = setup_browser(self.params['headless'])

            try:
                # Выполняем поиск
                self.statusUpdated.emit(
                    f"Поиск домена '{self.params['domain']}' по запросу '{self.params['query']}'...")
                self.progressUpdated.emit(20)

                result = search_yandex(driver,
                                       self.params['query'],
                                       self.params['domain'],
                                       self.params['pages'])

                if result:
                    self.statusUpdated.emit(f"Сайт найден на позиции {result['position']}, страница {result['page']}")
                    self.progressUpdated.emit(40)
                    self.searchCompleted.emit(result)

                    if self.is_cancelled:
                        safe_close_browser(driver)
                        return

                    # Переходим по ссылке
                    self.statusUpdated.emit("Переход по найденной ссылке...")
                    if click_search_result(driver, result["element"]):
                        self.progressUpdated.emit(50)

                        # Сохраняем текущий URL после перехода
                        target_site_url = driver.current_url

                        # Проверяем, что мы действительно перешли на целевой сайт
                        if is_yandex_url(driver.current_url):
                            self.statusUpdated.emit("Проверка перехода на сайт...")

                            # Проверяем, есть ли другие открытые окна
                            if len(driver.window_handles) > 1:
                                self.statusUpdated.emit(f"Проверка {len(driver.window_handles)} открытых окон...")

                                # Запоминаем текущее окно
                                current_window = driver.current_window_handle
                                target_window = None

                                # Проверяем все окна, ищем целевой сайт
                                for window_handle in driver.window_handles:
                                    if window_handle != current_window:
                                        driver.switch_to.window(window_handle)

                                        # Если URL содержит домен, который мы ищем
                                        if self.params['domain'] in driver.current_url or not is_yandex_url(
                                                driver.current_url):
                                            self.statusUpdated.emit(
                                                f"Найден целевой сайт в другом окне: {driver.current_url}")
                                            target_window = window_handle
                                            target_site_url = driver.current_url
                                            break

                                # Если не нашли целевое окно, возвращаемся к исходному
                                if not target_window:
                                    self.statusUpdated.emit("Целевой сайт не найден в открытых окнах")
                                    safe_close_browser(driver)
                                    return

                        # Ищем телефон на начальной странице
                        self.statusUpdated.emit("Поиск телефона на начальной странице...")
                        self.progressUpdated.emit(60)
                        phone_number = find_and_copy_phone_number(driver, 5)

                        if phone_number:
                            save_phone_to_file(self.params['domain'], phone_number, PHONE_NUMBERS_FILE)
                            self.phoneFound.emit(phone_number)
                        else:
                            self.statusUpdated.emit("На начальной странице телефон не найден")

                        if self.is_cancelled:
                            safe_close_browser(driver)
                            return

                        # Активное взаимодействие с сайтом
                        self.statusUpdated.emit(
                            f"Начинаем взаимодействие с сайтом (уровень: {self.params['interaction']})...")
                        self.progressUpdated.emit(70)

                        # Проверим еще раз, что мы на целевом сайте
                        if is_yandex_url(driver.current_url):
                            self.statusUpdated.emit(
                                "Мы все еще на странице Яндекса, пытаемся перейти на целевой сайт...")
                            try:
                                driver.get(target_site_url)
                                time.sleep(3)
                            except:
                                self.statusUpdated.emit("Не удалось перейти на целевой сайт")
                                safe_close_browser(driver)
                                return

                        # Взаимодействие с сайтом
                        interaction_results = interact_with_site(
                            driver,
                            self.params['stay_time'],
                            self.params['interaction']
                        )

                        self.progressUpdated.emit(85)

                        # Если телефон не был найден ранее, пробуем найти после взаимодействия
                        if not phone_number:
                            self.statusUpdated.emit("Поиск телефона после взаимодействия с сайтом...")
                            phone_number = find_and_copy_phone_number(driver, 5)

                            if phone_number:
                                save_phone_to_file(self.params['domain'], phone_number, PHONE_NUMBERS_FILE)
                                self.phoneFound.emit(phone_number)
                            else:
                                self.statusUpdated.emit("Телефон не найден и после активного взаимодействия")

                        # Создаем скриншот
                        if self.params['make_screenshot']:
                            self.statusUpdated.emit("Создание скриншота...")
                            screenshot_file = make_screenshot(driver)
                            self.screenshotTaken.emit(screenshot_file)

                        self.statusUpdated.emit(
                            f"Взаимодействие завершено: посещено {len(interaction_results['visited_pages'])} страниц, выполнено {interaction_results['clicked_elements']} кликов, заполнено {interaction_results['filled_forms']} форм")

                else:
                    self.statusUpdated.emit(
                        f"Сайт с доменом '{self.params['domain']}' не найден в первых {self.params['pages']} страницах поиска")
                    self.searchFailed.emit(f"Домен не найден в выдаче")

                self.progressUpdated.emit(100)

            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                self.statusUpdated.emit(f"Ошибка: {str(e)}")
                self.searchFailed.emit(f"Ошибка: {str(e)}\n{error_details}")
            finally:
                self.statusUpdated.emit("Закрытие браузера...")
                safe_close_browser(driver)
                self.statusUpdated.emit("Операция завершена")

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            self.statusUpdated.emit(f"Критическая ошибка: {str(e)}")
            self.searchFailed.emit(f"Критическая ошибка: {str(e)}\n{error_details}")

    def cancel(self):
        """Отмена операции"""
        self.is_cancelled = True
        self.statusUpdated.emit("Отмена операции...")


class MainWindow(QMainWindow):
    """Главное окно приложения"""

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.search_worker = None

    def init_ui(self):
        """Инициализация пользовательского интерфейса"""
        self.setWindowTitle("SERP Parser - Анализатор поисковой выдачи Яндекса")
        self.setMinimumSize(900, 700)

        # Создаем центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Основной вертикальный макет
        main_layout = QVBoxLayout(central_widget)

        # Разделитель для верхней (настройки) и нижней (логи) частей
        splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(splitter)

        # ===== Верхняя часть - настройки =====
        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)

        # Группа настроек поиска
        search_group = QGroupBox("Параметры поиска")
        search_form = QFormLayout()

        # Поля для поискового запроса и домена
        self.query_input = QLineEdit()
        self.domain_input = QLineEdit()
        search_form.addRow("Поисковый запрос:", self.query_input)
        search_form.addRow("Искомый домен:", self.domain_input)

        # Количество страниц
        self.pages_spinbox = QSpinBox()
        self.pages_spinbox.setRange(1, 20)
        self.pages_spinbox.setValue(3)
        search_form.addRow("Количество страниц:", self.pages_spinbox)

        # Чекбокс для фонового режима
        self.headless_checkbox = QCheckBox("Запустить браузер в фоновом режиме")
        search_form.addRow("", self.headless_checkbox)

        search_group.setLayout(search_form)
        settings_layout.addWidget(search_group)

        # Группа настроек взаимодействия
        interaction_group = QGroupBox("Параметры взаимодействия с сайтом")
        interaction_form = QFormLayout()

        # Уровень взаимодействия
        self.interaction_combo = QComboBox()
        self.interaction_combo.addItems(["Низкий", "Средний", "Высокий"])
        self.interaction_combo.setCurrentIndex(1)  # По умолчанию "Средний"
        interaction_form.addRow("Уровень взаимодействия:", self.interaction_combo)

        # Время пребывания на сайте
        self.stay_time_spinbox = QSpinBox()
        self.stay_time_spinbox.setRange(5, 300)
        self.stay_time_spinbox.setValue(15)
        self.stay_time_spinbox.setSuffix(" сек")
        interaction_form.addRow("Время пребывания на сайте:", self.stay_time_spinbox)

        # Множитель задержки
        self.delay_spinbox = QDoubleSpinBox()
        self.delay_spinbox.setRange(0.5, 3.0)
        self.delay_spinbox.setValue(1.0)
        self.delay_spinbox.setSingleStep(0.1)
        interaction_form.addRow("Множитель задержки:", self.delay_spinbox)

        # Чекбокс для скриншота
        self.screenshot_checkbox = QCheckBox("Делать скриншот найденного сайта")
        self.screenshot_checkbox.setChecked(True)
        interaction_form.addRow("", self.screenshot_checkbox)

        interaction_group.setLayout(interaction_form)
        settings_layout.addWidget(interaction_group)

        # Кнопки управления
        buttons_layout = QHBoxLayout()

        self.start_button = QPushButton("Запустить поиск")
        self.start_button.clicked.connect(self.start_search)
        buttons_layout.addWidget(self.start_button)

        self.cancel_button = QPushButton("Отменить")
        self.cancel_button.clicked.connect(self.cancel_search)
        self.cancel_button.setEnabled(False)
        buttons_layout.addWidget(self.cancel_button)

        self.open_results_button = QPushButton("Открыть результаты")
        self.open_results_button.clicked.connect(self.open_results_file)
        buttons_layout.addWidget(self.open_results_button)

        settings_layout.addLayout(buttons_layout)

        # Прогресс-бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        settings_layout.addWidget(self.progress_bar)

        # Добавляем виджет настроек в сплиттер
        splitter.addWidget(settings_widget)

        # ===== Нижняя часть - логи и результаты =====
        self.tabs = QTabWidget()

        # Вкладка логов
        self.log_tab = QWidget()
        log_layout = QVBoxLayout(self.log_tab)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setLineWrapMode(QTextEdit.NoWrap)
        log_layout.addWidget(self.log_text)

        # Настраиваем перенаправление логов
        self.log_redirector = LogRedirector(self.log_text)
        self.logger = self.log_redirector.logger

        self.tabs.addTab(self.log_tab, "Логи")

        # Вкладка результатов
        self.results_tab = QWidget()
        results_layout = QVBoxLayout(self.results_tab)

        # Информация о найденном сайте
        site_info_group = QGroupBox("Информация о найденном сайте")
        site_info_layout = QFormLayout()

        self.position_label = QLabel("-")
        self.url_label = QLabel("-")
        self.title_label = QLabel("-")

        site_info_layout.addRow("Позиция:", self.position_label)
        site_info_layout.addRow("URL:", self.url_label)
        site_info_layout.addRow("Заголовок:", self.title_label)

        site_info_group.setLayout(site_info_layout)
        results_layout.addWidget(site_info_group)

        # Информация о телефоне
        phone_group = QGroupBox("Найденный телефон")
        phone_layout = QFormLayout()

        self.phone_label = QLabel("-")
        self.phone_copy_button = QPushButton("Скопировать")
        self.phone_copy_button.clicked.connect(self.copy_phone_to_clipboard)
        self.phone_copy_button.setEnabled(False)

        phone_layout.addRow("Номер:", self.phone_label)
        phone_layout.addRow("", self.phone_copy_button)

        phone_group.setLayout(phone_layout)
        results_layout.addWidget(phone_group)

        # Информация о скриншоте
        screenshot_group = QGroupBox("Скриншот")
        screenshot_layout = QVBoxLayout()

        self.screenshot_path_label = QLabel("Скриншот не создан")
        self.open_screenshot_button = QPushButton("Открыть скриншот")
        self.open_screenshot_button.clicked.connect(self.open_screenshot)
        self.open_screenshot_button.setEnabled(False)

        screenshot_layout.addWidget(self.screenshot_path_label)
        screenshot_layout.addWidget(self.open_screenshot_button)

        screenshot_group.setLayout(screenshot_layout)
        results_layout.addWidget(screenshot_group)

        # Добавляем растягивающийся пустой виджет, чтобы выровнять группы вверху
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        results_layout.addWidget(spacer)

        self.tabs.addTab(self.results_tab, "Результаты")

        # Добавляем вкладки в сплиттер
        splitter.addWidget(self.tabs)

        # Устанавливаем соотношение размеров сплиттера
        splitter.setSizes([300, 400])

        # Сообщение о статусе
        self.statusBar().showMessage("Готов к работе")

        # Логируем запуск приложения
        self.logger.info("SERP Parser запущен и готов к работе")

    def start_search(self):
        """Запуск процесса поиска"""
        # Проверка на пустые поля
        if not self.query_input.text().strip():
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, введите поисковый запрос")
            return

        if not self.domain_input.text().strip():
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, введите домен для поиска")
            return

        # Собираем параметры
        params = {
            'query': self.query_input.text().strip(),
            'domain': self.domain_input.text().strip(),
            'pages': self.pages_spinbox.value(),
            'headless': self.headless_checkbox.isChecked(),
            'interaction': ['low', 'medium', 'high'][self.interaction_combo.currentIndex()],
            'stay_time': self.stay_time_spinbox.value(),
            'delay_factor': self.delay_spinbox.value(),
            'make_screenshot': self.screenshot_checkbox.isChecked()
        }

        # Очищаем предыдущие результаты
        self.clear_results()

        # Логируем начало операции
        self.logger.info(f"Начинаем поиск домена '{params['domain']}' по запросу '{params['query']}'")
        self.logger.info(
            f"Параметры: страниц - {params['pages']}, режим - {'фоновый' if params['headless'] else 'видимый'}")
        self.logger.info(
            f"Взаимодействие: уровень - {params['interaction']}, время - {params['stay_time']} сек, задержка - {params['delay_factor']}x")

        # Создаем и запускаем рабочий поток
        self.search_worker = SearchWorker(params)

        # Подключаем сигналы
        self.search_worker.progressUpdated.connect(self.update_progress)
        self.search_worker.statusUpdated.connect(self.update_status)
        self.search_worker.searchCompleted.connect(self.handle_search_completed)
        self.search_worker.searchFailed.connect(self.handle_search_failed)
        self.search_worker.phoneFound.connect(self.handle_phone_found)
        self.search_worker.screenshotTaken.connect(self.handle_screenshot_taken)

        # Обновляем состояние UI
        self.start_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.progress_bar.setValue(0)
        self.statusBar().showMessage("Выполняется поиск...")

        # Запускаем поток
        self.search_worker.start()

    def cancel_search(self):
        """Отмена процесса поиска"""
        if self.search_worker and self.search_worker.isRunning():
            reply = QMessageBox.question(
                self,
                'Подтверждение',
                'Вы уверены, что хотите прервать текущую операцию?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                self.logger.info("Отмена операции пользователем")
                self.search_worker.cancel()
                self.statusBar().showMessage("Отмена операции...")

    def update_progress(self, value):
        """Обновление прогресс-бара"""
        self.progress_bar.setValue(value)

    def update_status(self, status):
        """Обновление статуса в лог"""
        self.logger.info(status)
        self.statusBar().showMessage(status)

    def handle_search_completed(self, result):
        """Обработка успешного поиска"""
        self.position_label.setText(f"{result['position']} (страница {result['page']})")
        self.url_label.setText(result['url'])
        self.title_label.setText(result['title'])

        # Переключаемся на вкладку результатов
        self.tabs.setCurrentIndex(1)

    def handle_search_failed(self, error_message):
        """Обработка ошибки при поиске"""
        self.logger.info(f"Ошибка: {error_message}")
        QMessageBox.warning(self, "Ошибка поиска", error_message)

        # Восстанавливаем состояние UI
        self.start_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.statusBar().showMessage("Готов к работе")

    def handle_phone_found(self, phone):
        """Обработка найденного телефона"""
        self.phone_label.setText(phone)
        self.phone_copy_button.setEnabled(True)
        self.logger.info(f"Найден телефон: {phone}")

    def handle_screenshot_taken(self, screenshot_path):
        """Обработка созданного скриншота"""
        self.screenshot_path_label.setText(screenshot_path)
        self.open_screenshot_button.setEnabled(True)
        self.logger.info(f"Создан скриншот: {screenshot_path}")

    def copy_phone_to_clipboard(self):
        """Копирование телефона в буфер обмена"""
        phone = self.phone_label.text()
        if phone and phone != "-":
            clipboard = QApplication.clipboard()
            clipboard.setText(phone)
            self.statusBar().showMessage(f"Телефон {phone} скопирован в буфер обмена", 3000)

    def open_screenshot(self):
        """Открытие сохраненного скриншота"""
        screenshot_path = self.screenshot_path_label.text()
        if os.path.exists(screenshot_path):
            # Используем стандартное приложение для открытия изображения
            import subprocess
            import platform

            system = platform.system()
            try:
                if system == 'Darwin':  # macOS
                    subprocess.call(('open', screenshot_path))
                elif system == 'Windows':
                    os.startfile(screenshot_path)
                else:  # Предположительно Linux
                    subprocess.call(('xdg-open', screenshot_path))

                self.logger.info(f"Открыт скриншот: {screenshot_path}")
            except Exception as e:
                self.logger.info(f"Ошибка при открытии скриншота: {str(e)}")
                QMessageBox.warning(self, "Ошибка", f"Не удалось открыть скриншот: {str(e)}")
        else:
            self.logger.info(f"Скриншот не найден: {screenshot_path}")
            QMessageBox.warning(self, "Файл не найден", f"Скриншот не найден: {screenshot_path}")

    def open_results_file(self):
        """Открытие файла с результатами"""
        from config import PHONE_NUMBERS_FILE

        if os.path.exists(PHONE_NUMBERS_FILE):
            # Используем стандартное приложение для открытия текстового файла
            import subprocess
            import platform

            system = platform.system()
            try:
                if system == 'Darwin':  # macOS
                    subprocess.call(('open', PHONE_NUMBERS_FILE))
                elif system == 'Windows':
                    os.startfile(PHONE_NUMBERS_FILE)
                else:  # Предположительно Linux
                    subprocess.call(('xdg-open', PHONE_NUMBERS_FILE))

                self.logger.info(f"Открыт файл результатов: {PHONE_NUMBERS_FILE}")
            except Exception as e:
                self.logger.info(f"Ошибка при открытии файла результатов: {str(e)}")
                QMessageBox.warning(self, "Ошибка", f"Не удалось открыть файл: {str(e)}")
        else:
            self.logger.info(f"Файл результатов не найден: {PHONE_NUMBERS_FILE}")
            QMessageBox.warning(self, "Файл не найден", f"Файл с телефонами не найден: {PHONE_NUMBERS_FILE}")

    def clear_results(self):
        """Очистка результатов"""
        self.position_label.setText("-")
        self.url_label.setText("-")
        self.title_label.setText("-")
        self.phone_label.setText("-")
        self.phone_copy_button.setEnabled(False)
        self.screenshot_path_label.setText("Скриншот не создан")
        self.open_screenshot_button.setEnabled(False)

    def closeEvent(self, event):
        """Обработка закрытия окна"""
        # Проверяем, есть ли активный процесс
        if self.search_worker and self.search_worker.isRunning():
            reply = QMessageBox.question(
                self,
                'Подтверждение',
                'Выполняется поиск. Вы уверены, что хотите выйти?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                # Отменяем операцию
                self.search_worker.cancel()
                # Даем небольшую паузу для корректного завершения
                self.search_worker.wait(1000)
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def main():
    """Основная функция приложения"""
    app = QApplication(sys.argv)

    # Установка стилей
    app.setStyle("Fusion")

    # Создание и отображение главного окна
    main_window = MainWindow()
    main_window.show()

    sys.exit(app.exec_())


# Если запускается напрямую, создаем приложение
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Установка стилей
    app.setStyle("Fusion")

    # Создание и отображение главного окна
    main_window = MainWindow()
    main_window.show()

    sys.exit(app.exec_())