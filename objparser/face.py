class Face:

    def __init__(self, vertex1, vertex2, vertex3, vt1_idx=0, vt2_idx=0, vt3_idx=0, vn_idx=0):
        # direct reference to corresponding vertex
        self.vertices = [vertex1, vertex2, vertex3]
        # index of texture
        self.vt_indices = [vt1_idx, vt2_idx, vt3_idx]
        # the normal is considered constant for the whole face, we only need to save it once
        self.vn_idx = vn_idx
