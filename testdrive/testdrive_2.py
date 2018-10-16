
import moderngl as mg
from PySide import QtWidgets
from PyQt5.QtCore import Qt


class Tool(QtWidgets.QOpenGLWidget):
    def __init__(self, mainwin):
        super(Tool, self).__init__(mainwin)


app = QtWidgets.QApplication([])
mainwin = QtWidgets.QMainWindow(None, Qt.WindowStaysOnTopHint)
Tool(mainwin)
mainwin.show()
app.exec()
