import sys

from PyQt5.QtWidgets import QApplication

from src.gui.ui import NikkeOCRUI
from src.utils.localization import set_language


def main():
    app = QApplication(sys.argv)
    set_language("en")

    window = NikkeOCRUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
