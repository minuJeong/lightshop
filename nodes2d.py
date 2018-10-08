
from _glloader import _Loader


class PassThrough2D(_Loader):
    def __init__(self, gl_context, img):
        super(PassThrough2D, self).__init__()

        self.context = gl_context
        self.build_quad_vao(self.context, img, "./gl/passthrough2d.frag")

    def render(self):
        self.texture.use(0)
        self.vao.render()


class DepthToNormal(_Loader):
    def __init__(self, gl_context, img):
        super(DepthToNormal, self).__init__()
        self.context = gl_context
        self.build_quad_vao(self.context, img, "./gl/depth_to_normal.frag")

    def render(self):
        self.texture.use(0)
        self.context.vertex_array(self.program, self.vbo, self.ibo).render()
