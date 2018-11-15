
"""
headless rendering with moderngl
author: minu jeong
"""

import sys
import time
from threading import Thread
from queue import Queue
from threading import Event

import numpy as np
import moderngl as mg
import imageio as ii


class ProgramPool(object):
    def __init__(self, context):
        self._programs = {}
        self._cache = {}
        self.context = context

        self._programs["uvdebug"] = (
            self._load('./gl/testdrives/vs_simple.glsl'),
            self._load('./gl/testdrives/fs_uvdebug.glsl')
        )

    def _load(self, filename):
        if filename in self._cache.keys():
            return self._cache[filename]

        with open(filename, 'r') as fp:
            ctx = fp.read()
        return ctx

    def get(self, key):
        if key in self._programs.keys():
            vs, fs = self._programs[key]
            return self.context.program(vertex_shader=vs, fragment_shader=fs)
        raise Exception(f"program key is not found: {key}")


class Recorder(Thread):
    data_queue = Queue()
    finish_event = Event()

    def __init__(self, dst_path):
        super(Recorder, self).__init__()
        self.dst_path = dst_path

    def run(self):
        """
        using multithread for dev (sublime IDE)
        use multiprocessing package for production
        (Thread -> Process)
        """
        print("recorder daemon started,")

        writer = ii.get_writer(self.dst_path, fps=60)
        while not self.finish_event.is_set():
            while not self.data_queue.empty():
                next_data = self.data_queue.get(False)
                if next_data is not None:
                    writer.append_data(next_data)
            time.sleep(.100)
        writer.close()
        print("finished recording everything, closed writer!")


class Renderer(object):
    scene_nodes = []

    def __init__(self):
        super(Renderer, self)

        self.W, self.H = 1, 1
        self.render_size = (1, 1)

    def init(self, W=512, H=512):
        print("initializing..")

        self.W, self.H = W, H
        self.render_size = (self.W, self.H)
        self.context = mg.create_standalone_context()

        self.init_scene()

        self.output_texture = self.context.texture(self.render_size, 4, dtype='f4')
        self.framebuffer = self.context.framebuffer(self.output_texture)
        self.framebuffer.use()

        print("initialized context!")
        return self

    def init_scene(self):
        prog_pool = ProgramPool(self.context)
        self.add_mesh(
            prog_pool.get('uvdebug'),
            np.array([
                -1.0, -1.0, +0.0,  -1, -1,
                -1.0, +1.0, +0.0,  -1, +1,
                +1.0, -1.0, +0.0,  +1, -1,
                +1.0, +1.0, +0.0,  +1, +1,
            ]),
            np.array([
                0, 1, 2, 1, 2, 3
            ]))
        return self

    def add_mesh(self, program, verts, indices):
        vao = self.context.vertex_array(
            program,
            [(
                self.context.buffer(verts.astype('f4').tobytes()),
                "3f 2f",
                "in_verts", "in_uvs"
            )],
            self.context.buffer(indices.astype('i4').tobytes()))
        program["u_projection"].value = \
            (1, 0, 0, 0,  0, 1, 0, 0,  0, 0, 1, 0,  0, 0, 0, 1)
        program["u_view"].value = \
            (1, 0, 0, 0,  0, 1, 0, 0,  0, 0, 1, 0,  0, 0, 0, 1)
        program["u_model"].value = \
            (1, 0, 0, 0,  0, 1, 0, 0,  0, 0, 1, 0,  0, 0, 0, 1)
        program['u_resolution'].value = (self.W, self.H, 0, 0)
        self.scene_nodes.append(vao)
        return vao

    def render(self, frame_idx):
        for vao in self.scene_nodes:
            if 'u_frame' in vao.program:
                vao.program['u_frame'].value = frame_idx
            vao.render()
        return self

    def render_pipeline(self):
        print("initializing recorder..")
        recorder = Recorder("./result.mp4")
        recorder.start()

        print("start rendering..")
        LEN = 500
        for i in range(LEN):
            # print progress rewriting line,
            [
                sys.stdout.write('\r'),
                sys.stdout.flush(),
                sys.stdout.write(f"rendering {i} / {LEN}..\r")
            ]

            self.render(i)

            serial_data = self.output_texture.read()
            data = np.frombuffer(serial_data, dtype='f4')
            data = data * 255.0
            data = data.astype(np.uint8)
            data = data.reshape((*self.render_size, 4))
            data = data[::-1]
            recorder.data_queue.put(data)

        print("rendering finished!")
        print("waiting for writer..")
        recorder.finish_event.set()

        recorder.join()
        print("writer finished!")
        return self

if __name__ == "__main__":
    Renderer().init().render_pipeline()
    print("everything done!")
