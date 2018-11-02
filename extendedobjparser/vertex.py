class Vertex(object):

    def __init__(self, v_idx, vt_idx=None, vn_idx=None):
        self.v_idx = v_idx      # index of vertex
        self.vt_idx = vt_idx    # index of texture coordinate
        self.vn_idx = vn_idx    # index of normal

    def has_texture(self):
        return self.vt_idx is not None

    def has_normal(self):
        return self.vn_idx is not None
