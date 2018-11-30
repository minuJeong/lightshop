    
import numpy as np
import moderngl as mg

from PIL import Image
from PIL.ImageQt import ImageQt

from PyQt5 import QtWidgets
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QThread
from PyQt5.QtCore import pyqtSignal

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from _common import _read
from _common import _screen_quad
from _common import _flatten_array


def _screenspace_generation(width, height):
    vs = _read("./gl/gradient_fresnel_tex.vs")
    fs = _read("./gl/_debug.fs")

    context = mg.create_standalone_context()
    program = context.program(vertex_shader=vs, fragment_shader=fs)
    vao = _screen_quad(program, context)

    test_texture = context.texture((width, height), 4)
    test_texture.use(0)

    frame_tex = context.texture((width, height), 4, dtype='f4')
    frame = context.framebuffer([frame_tex])
    frame.use()

    vao.render()
    result_bytes = frame_tex.read()

    data = np.frombuffer(result_bytes, dtype='f4')
    data = data.reshape((height, width, 4))
    return _flatten_array(data)


def _compute_driven_generation(width, height, cs_path):
    x, y, z = 1024, 1, 1
    args = {
        'X': x,
        'Y': y,
        'Z': z,
        'WIDTH': width,
        'HEIGHT': height,
    }
    cs = _read(cs_path, args)

    context = mg.create_standalone_context()
    compute_shader = context.compute_shader(cs)

    in_data = np.random.uniform(0.0, 1.0, (width, height, 4))
    out_data = np.zeros((width, height, 4))

    in_buffer = context.buffer(in_data.astype('f4'))
    in_buffer.bind_to_storage_buffer(0)

    out_buffer = context.buffer(out_data.astype('f4'))
    out_buffer.bind_to_storage_buffer(1)

    compute_shader.run(x, y, z)

    data = np.frombuffer(out_buffer.read(), dtype='f4')
    data = data.reshape((height, width, 4))
    return _flatten_array(data)


class QtObserver(QThread):
    ''' glues qt thread with watchdog observer thread '''

    signal_glue = pyqtSignal()

    def __init__(self, watch_path):
        super(QtObserver, self).__init__()

        self.watch_path = watch_path

    def on_watch(self):
        self.signal_glue.emit()

    def run(self):
        observer = Observer()

        event_handler = OnChangeHandler(self.on_watch)
        observer.schedule(event_handler, self.watch_path)
        observer.start()

        observer.join()


class OnChangeHandler(FileSystemEventHandler):
    def __init__(self, on_mod_callback):
        self.on_mod_callback = on_mod_callback
        self.on_mod_callback()

    def on_modified(self, event):
        self.on_mod_callback()


class ComputeShaderViewer(QtWidgets.QLabel):
    def __init__(self, size):
        super(ComputeShaderViewer, self).__init__()

        self.size = size
        self.shader_path = "./gl/tex_gen/compute_median.glsl"
        self.watch_path = "./gl/tex_gen/"

        self.observer = QtObserver(self.watch_path)
        self.observer.signal_glue.connect(self.recompile_compute_shader)
        self.observer.start()

    def recompile_compute_shader(self):
        try:
            data = _compute_driven_generation(width, height, self.shader_path)
            img = Image.fromarray(data)
            pixmap = QPixmap.fromImage(ImageQt(img))
            self.setPixmap(pixmap)
            self.setAlignment(Qt.AlignCenter)
        except Exception as e:
            print(e)

if __name__ == "__main__":
    width, height = 1024, 1024

    app = QtWidgets.QApplication([])
    win = ComputeShaderViewer((width, height))
    win.setWindowFlags(Qt.WindowStaysOnTopHint)
    win.setMinimumSize(256, 256)
    win.show()

    app.exec()
