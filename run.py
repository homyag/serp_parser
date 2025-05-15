import sys
from ui_app import MainWindow
from PyQt5.QtWidgets import QApplication


def main():
    """Основная функция приложения"""
    app = QApplication(sys.argv)

    # Установка стилей
    app.setStyle("Fusion")

    # Создание и отображение главного окна
    main_window = MainWindow()
    main_window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()