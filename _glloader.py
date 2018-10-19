
import numpy as np


_cache = {}


def _load_file(file):
    if file in _cache:
        return _cache[file]

    with open(file, 'r') as fp:
        program = fp.read()

    _cache[file] = program
    return program


class _Loader(object):
    quad_verts = np.array([
        -1.0, -1.0,
        -1.0, +1.0,
        +1.0, -1.0,
        +1.0, +1.0,
    ]).astype('f4').tobytes()

    quad_uvs = np.array([
        0.0, 1.0,
        0.0, 0.0,
        1.0, 1.0,
        1.0, 0.0,
    ]).astype('f4').tobytes()

    quad_indices = np.array([
        0, 1, 2,
        1, 2, 3
    ]).astype('i4').tobytes()

    texture = None

    def build_quad_vao(self, context, img, frag_code):
        vtx_path = "./gl/passthrough2d.vert"
        frg_path = frag_code

        self.program = self.context.program(
            vertex_shader=_load_file(vtx_path), fragment_shader=_load_file(frg_path)
        )
        self.texture = self.context.texture(img.size, 4, img.tobytes())

        vbo_buffer = self.context.buffer(self.quad_verts)
        uv_buffer = self.context.buffer(self.quad_uvs)
        self.vbo = [
            (vbo_buffer, '2f', 'in_vert'),
            (uv_buffer, '2f', 'in_uvcoord')
        ]
        self.ibo = self.context.buffer(self.quad_indices)
        self.vao = self.context.vertex_array(self.program, self.vbo, self.ibo)
