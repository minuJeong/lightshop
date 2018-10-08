
import os
from functools import partial

import numpy as np
import moderngl as mgl

from PIL import Image
from psd_tools import PSDImage

from PyQt5 import QtWidgets
from PyQt5.Qt import Qt
from PyQt5.QtCore import QObject
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtCore import pyqtSignal

from nodes2d import PassThrough2D
from nodes2d import DepthToNormal
from ui.mainwindow import Ui_window


class PSDLoader(QObject):
    complete_load_signal = pyqtSignal()
    depth_img = None

    def refresh(self, psd_path):
        if not psd_path:
            print(f"PSDLoader: argument: psd_path is not given")
            return

        if not os.path.isfile(psd_path):
            print(f"PSDLoader: can't find file at {psd_path}")
            return

        psd_img = PSDImage.load(psd_path)

        if not psd_img:
            print(f"PSDLoader: can't load psd image at {psd_path}")
            return

        for root_layer in psd_img.layers:
            if root_layer.name.lower() == "depth":
                self.depth_img = root_layer.as_PIL()

        self.complete_load_signal.emit()


class NodeWidget(QtWidgets.QOpenGLWidget):
    i = 0
    context = None
    viewport = (0, 0, 0, 0)

    def __init__(self):
        super(NodeWidget, self).__init__()

    def init_node(self):
        raise NotImplemented

    def render(self):
        raise NotImplemented

    def paintGL(self):
        self.context.clear(0.0, 0.0, 0.5)
        self.context.viewport = self.viewport
        self.render()
        self.update()

    def initializeGL(self):
        if not self.context:
            self.context = mgl.create_context()
        self.init_node()

class DepthmapNode(NodeWidget):
    def __init__(self):
        super(DepthmapNode, self).__init__()

    def init_node(self, img=None):
        if not img:
            img = Image.new("RGBA", (1, 1))
        self.device = PassThrough2D(self.context, img)
        self.viewport = (0, 0, 5, 5)

    def render(self):
        self.device.render()

    # called by qt framework
    def mousePressEvent(self, e):
        print(self, "click", self.context)


class NormalmapNode(NodeWidget):
    def __init__(self):
        super(NormalmapNode, self).__init__()

    def init_node(self, img=None):
        if not img:
            img = Image.new("RGBA", (1, 1))
        self.device = DepthToNormal(self.context, img)

    def render(self):
        # self.device.render()
        pass

    # called by qt framework
    def mousePressEvent(self, e):
        print(self, "click", self.context)


class Tool(QObject):
    depthmap_update_signal = pyqtSignal()
    normalmap_update_signal = pyqtSignal()

    depth_node = None
    normalmap_node = None

    _path = "D:/Box/Box Sync/Drawing/DRAW_2018/10/sfjifjsi333311117676786.psd"

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, path):
        self._path = path

    def __init__(self, tool_window):
        super(Tool, self).__init__()
        self.psdloader = PSDLoader()
        self.psdloader.complete_load_signal.connect(lambda: print("finish refresh psd"))

    def refresh_psd(self):
        """ read psd file again """
        self.psdloader.refresh(self.path)

        if self.depth_node:
            self.depth_node.init_node(
                self.psdloader.depth_img
            )

        if self.normalmap_node:
            self.depth_node.init_node(
                self.psdloader.depth_img
            )


class ToolWindow(Ui_window, QObject):
    tool = None

    def __init__(self, qt_win):
        super(ToolWindow, self).__init__()
        Ui_window.setupUi(self, qt_win)

        self.tool = Tool(self)
        self.tool.depth_node = DepthmapNode()
        self.tool.normalmap_node = NormalmapNode()

        self.le_psdpath.setText(self.tool.path)
        self.hl_canvasgroup.addWidget(self.tool.depth_node)
        self.hl_canvasgroup.addWidget(self.tool.normalmap_node)

        self.b_exit.clicked.connect(partial(self.b_exit_clicked, qt_win))
        self.b_refresh.clicked.connect(self.refresh_psd)

    def b_exit_clicked(self, qt_win, clicked=False):
        qt_win.close()

    def refresh_psd(self, clicked=False):
        self.tool.refresh_psd()


def main():
    app = QtWidgets.QApplication([])
    qt_win = QtWidgets.QMainWindow(None, Qt.WindowStaysOnTopHint)
    ToolWindow(qt_win)
    qt_win.show()
    app.exec()


if __name__ == "__main__":
    main()
