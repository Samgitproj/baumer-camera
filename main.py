import sys
from PyQt5.QtWidgets import QApplication
from gui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)

    # Maak en toon hoofdvenster direct in fullscreen-modus met titelbalk
    window = MainWindow()
    window.showMaximized()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
