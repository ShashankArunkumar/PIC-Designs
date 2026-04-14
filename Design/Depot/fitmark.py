from PyQt5 import QtCore, QtWidgets

try:
    from ui.mainwindow import MainWindow
except ModuleNotFoundError:
    class MainWindow(QtWidgets.QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("fitmark")
            self.resize(800, 600)

            label = QtWidgets.QLabel(
                "ui.mainwindow is missing from this workspace.\n"
                "Install or generate the UI package to restore the full app.",
                alignment=QtCore.Qt.AlignCenter,
            )
            self.setCentralWidget(label)

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    ui = MainWindow()
    ui.show()
    sys.exit(app.exec_())

