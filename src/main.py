import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

from src.selector import OTClientSelector

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Light gray palette
    from PyQt5.QtGui import QPalette, QColor
    light_palette = QPalette()
    light_palette.setColor(QPalette.Window, QColor(240, 240, 240))
    light_palette.setColor(QPalette.WindowText, Qt.black)
    light_palette.setColor(QPalette.Base, QColor(250, 250, 250))
    light_palette.setColor(QPalette.AlternateBase, QColor(235, 235, 235))
    light_palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
    light_palette.setColor(QPalette.ToolTipText, Qt.black)
    light_palette.setColor(QPalette.Text, Qt.black)
    light_palette.setColor(QPalette.Button, QColor(245, 245, 245))
    light_palette.setColor(QPalette.ButtonText, Qt.black)
    light_palette.setColor(QPalette.BrightText, Qt.red)
    light_palette.setColor(QPalette.Link, QColor(42, 130, 218))
    light_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    light_palette.setColor(QPalette.HighlightedText, Qt.white)

    app.setPalette(light_palette)

    window = OTClientSelector()
    window.show()
    sys.exit(app.exec_())
