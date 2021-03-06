
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
        self.viewport = (0, 0, self.width() - 20, self.height() - 20)

    def init_node(self):
        raise NotImplemented

    def render(self):
        raise NotImplemented

    def paintGL(self):
        self.context.viewport = self.viewport
        self.render()
        self.update()

    def initializeGL(self):
        if not self.context:
            self.context = mgl.create_context()
        self.context.clear(0.0, 0.0, 0.5)
        self.init_node()

class NormalmapNode(NodeWidget):
    def __init__(self):
        super(NormalmapNode, self).__init__()

    def init_node(self):
        size = (512, 512)
        channels = 3
        array = np.random.uniform(0, 255, (*size, channels)).astype(np.uint8)
        img = Image.fromarray(array)
        aspect = self.width() / self.height()
        self.device = DepthToNormal(self.context, img, aspect)

    def render(self):
        self.device.render()

        size = (512, 512)
        channels = 3

        fb = self.context.simple_framebuffer(size)
        fb.use()
        self.device.render()

        fb_data = fb.read()
        img = Image.frombytes("RGB", size, fb_data)
        img.transpose(Image.ROTATE_90)

        array = np.random.uniform(0, 255, (*size, channels)).astype(np.uint8)
        add_img = Image.fromarray(array)

        img = Image.blend(img, add_img, 0.2)
        self.device.rebuild_texture(img)

    # called by qt framework
    def mousePressEvent(self, e):
        print(self, "click", self.context)


class Tool(QObject):
    normalmap_node = None

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, path):
        self._path = path

    def __init__(self, tool_window):
        super(Tool, self).__init__()


class ToolWindow(Ui_window, QObject):
    tool = None

    def __init__(self, qt_win):
        super(ToolWindow, self).__init__()
        Ui_window.setupUi(self, qt_win)

        self.qt_win = qt_win

        self.tool = Tool(self)
        self.tool.normalmap_node = NormalmapNode()

        self.hl_canvasgroup.addWidget(self.tool.normalmap_node)

        self.b_exit.clicked.connect(lambda e: qt_win.close())
        self.b_refresh.clicked.connect(self.refresh_psd)

    def refresh_psd(self, clicked=False):
        print('not implemented')


def main():
    app = QtWidgets.QApplication([])
    qt_win = QtWidgets.QMainWindow(None, Qt.WindowStaysOnTopHint)
    tool = ToolWindow(qt_win)
    qt_win.show()
    app.exec()


if __name__ == "__main__":
    main()
