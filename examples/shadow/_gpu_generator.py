
import os
import time
import math

import numpy as np
import moderngl as mg
import imageio as ii

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


def _screenspace_generation(
            width, height,
            vspath, fspath,
            start_time=0.0, end_time=1.0, frames=1,
            **uniforms
        ):
    vs = _read(vspath)
    fs = _read(fspath)

    context = mg.create_standalone_context()
    program = context.program(vertex_shader=vs, fragment_shader=fs)
    vao = _screen_quad(program, context)

    for k, v in uniforms.items():
        if k not in program:
            continue

        program[k].value = v

    test_texture = context.texture((width, height), 4)
    test_texture.use(0)

    frame_tex = context.texture((width, height), 4, dtype='f4')
    frame = context.framebuffer([frame_tex])
    frame.use()

    u_time = {"value": 0.0}
    if "u_time" in program:
        u_time = program["u_time"]

    span = end_time - start_time
    step = span / max(float(frames), 0.0)
    for t in range(int(frames)):
        u_time.value = start_time + step * t

        vao.render()
        result_bytes = frame_tex.read()

        data = np.frombuffer(result_bytes, dtype='f4')
        data = data.reshape((height, width, 4))
        yield _flatten_array(data)


def _compute_driven_generation(width, height, cs_path):
    x, y, z = 1024, 1, 1
    cs_args = {
        'X': x,
        'Y': y,
        'Z': z,
        'WIDTH': width,
        'HEIGHT': height,
    }

    cs = _read(cs_path, cs_args)

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
        observer.schedule(event_handler, self.watch_path, recursive=True)
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
        self.shader_path = "./gl/tex_gen/step_texture.glsl"
        self.watch_path = "./gl/tex_gen/"

        self.observer = QtObserver(self.watch_path)
        self.observer.signal_glue.connect(self.recompile_compute_shader)
        self.observer.start()

    def recompile_compute_shader(self):
        try:
            data = _compute_driven_generation(self.size[0], self.size[1], self.shader_path)
            img = Image.fromarray(data)
            pixmap = QPixmap.fromImage(ImageQt(img))
            self.setPixmap(pixmap)
            self.setAlignment(Qt.AlignCenter)
        except Exception as e:
            print(e)

    def keyPressEvent(self, e=None):
        if e.key() == Qt.Key_Space:
            data = _compute_driven_generation(self.size[0], self.size[1], self.shader_path)
            img = Image.fromarray(data)
            img.save("GPU_Generated.png")


class FragmentWatcher(QtWidgets.QOpenGLWidget):
    def __init__(self, size):
        super(FragmentWatcher, self).__init__()

        self.size = size
        self.setMinimumSize(size[0], size[1])
        self.setMaximumSize(size[0], size[1])
        self.watch_path = "./_gl/"

        self.vao = None

    def recompile_shaders(self, path="./_gl/pikachu"):
        print("recompiling shaders..")

        try:
            vs = _read("{}/verts.glsl".format(path))
            fs = _read("{}/frags.glsl".format(path))

            program = self.context.program(vertex_shader=vs, fragment_shader=fs)
            self.u_time = program["u_time"]
            self.u_campos = program["u_campos"]
            self.u_campos.value = (0.0, 0.0, -10.0)

            self.u_focus = program["u_focus"]
            self.u_focus.value = (0.0, 2.0, 0.0)

            self.vao = _screen_quad(program, self.context)

        except Exception as e:
            print("failed to compile shaders, {}".format(e))
            return

        print("recompiled shaders!")

    def initializeGL(self):
        self.context = mg.create_context()
        self.start_time = time.time()
        self.recompile_shaders()

        self.observer = QtObserver(self.watch_path)
        self.observer.signal_glue.connect(self.recompile_shaders)
        self.observer.start()

    def paintGL(self):
        if self.vao:
            t = time.time() - self.start_time
            self.u_time.value = t
            x = math.cos(t) * +10.0
            z = math.sin(t) * -10.0
            self.u_campos.value = (x, 0.0, z)
            self.vao.render()
            self.update()


class Tool(QtWidgets.QWidget):

    def __init__(self, width, height):
        super(Tool, self).__init__()

        root_layout = QtWidgets.QVBoxLayout()
        self.setLayout(root_layout)
        root_layout.setContentsMargins(0, 0, 0, 0)

        shaders_layout = QtWidgets.QVBoxLayout()
        root_layout.addLayout(shaders_layout)
        shaders_layout.setContentsMargins(0, 0, 0, 0)

        self.path_le = QtWidgets.QLineEdit()
        shaders_layout.addWidget(self.path_le)
        self.path_le.setText("./_gl/pikachu")

        self.renderer = FragmentWatcher((width, height))
        root_layout.addWidget(self.renderer)

        self.path_le.returnPressed.connect(self.recompile)

    def recompile(self):
        path = self.path_le.text()
        self.renderer.recompile_shaders(path)


def main():
    if True:
        if not os.path.isdir("pika"):
            os.makedirs("pika")

        u_campos = (0.0, 0.0, -10.0)
        u_focus = (0.0, 2.0, 0.0)

        if False:
            gif_writer = ii.get_writer("./pika/pikachu.gif", fps=24)
            mp4_writer = ii.get_writer("./pika/pikachu.mp4", fps=24)
            for data in _screenspace_generation(
                    304, 304,
                    "./_gl/pikachu/verts.glsl",
                    "./_gl/pikachu/frags.glsl",
                    start_time=2.4, end_time=8.64316, frames=64,
                    u_campos=u_campos, u_focus=u_focus):
                gif_writer.append_data(data)
                mp4_writer.append_data(data)

        if True:
            atlas_resolution = 2048
            n_row = 5
            w = atlas_resolution // n_row
            atlas = Image.new("RGBA", (2048, 2048))

            half = 0.5 / n_row
            distance = 10.0
            pi = math.pi
            for i in range(n_row * n_row):
                u = i % n_row
                v = i // n_row

                ur = u / n_row + half
                vr = v / n_row + half

                yr = abs(0.5 - vr) * 2.0
                xzr = math.cos(math.atan2(yr, 1.0))
                ra = 2.0 * -pi * ur

                x = math.cos(ra) * distance * xzr
                y = yr * distance
                z = math.sin(ra) * distance * xzr

                # todo: campos inplace to pipeline
                u_campos = (x, y, z)
                for data in _screenspace_generation(
                        w, w,
                        "./_gl/pikachu/verts.glsl",
                        "./_gl/pikachu/frags.glsl",
                        u_campos=u_campos, u_focus=u_focus):

                    x = i % n_row
                    y = i // n_row
                    img = Image.fromarray(data)
                    paste_at = (u * w, v * w)
                    atlas.paste(img, paste_at)
            atlas.save("./pika/T_PikachuAtlas.png")

        if False:
            i = 0
            for data in _screenspace_generation(
                    300, 300,
                    "./_gl/pikachu/verts.glsl",
                    "./_gl/pikachu/frags.glsl",
                    start_time=2.4, end_time=2.2,
                    u_campos=u_campos, u_focus=u_focus):
                ii.imwrite("./pika/pikachu_{}.png".format(i), data)
                i += 1

        return

    width, height = 200, 200

    app = QtWidgets.QApplication([])
    mainwin = QtWidgets.QMainWindow()
    mainwin.setWindowTitle("Pikachu Renderer")

    tool = Tool(width, height)
    mainwin.setCentralWidget(tool)
    mainwin.setWindowFlags(Qt.WindowStaysOnTopHint)
    mainwin.show()

    app.exec()

if __name__ == "__main__":
    main()
