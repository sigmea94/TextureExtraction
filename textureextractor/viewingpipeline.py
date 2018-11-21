import numpy as np


class Pipeline:

    def __init__(self, camera, vertices):
        self.vertices = []
        self.set_vertices(vertices)

        look = np.array(camera["look_direction"])
        self.w = look / np.linalg.norm(look)

        # up direction is considered given
        up = np.array([0, 1, 0])
        cross = np.cross(up, self.w)
        self.u = cross / np.linalg.norm(cross)
        self.v = np.cross(self.w, self.u)
        self.camera_pos = np.array(camera["position"])

    def set_vertices(self, vertices):
        # homogenize vertices and add to list
        self.vertices = []
        for v in vertices:
            self.vertices.append(np.append(np.array(v), np.array([1])))

    def get_vertices(self):
        res = []
        for v in self.vertices:
            res.append(np.delete(v, 3).tolist())
        return res

    def apply_to_scene(self, scene):
        # add transformed vertices and normals to scene
        for i, v in enumerate(self.get_vertices()):
            scene.vertices[i].pos = v

    def apply_view_transformation(self):
        t_an = np.identity(4)
        t_an[0][3] = -self.camera_pos[0]
        t_an[1][3] = -self.camera_pos[1]
        t_an[2][3] = -self.camera_pos[2]

        m_an = np.array([[self.u[0], self.u[1], self.u[2], 0],
                             [self.v[0], self.v[1], self.v[2], 0],
                             [self.w[0], self.w[1], self.w[2], 0],
                             [0, 0, 0, 1]])

        view_mat = np.matmul(m_an, t_an)

        for i, v in enumerate(self.vertices):
            self.vertices[i] = np.matmul(view_mat, v)

    def apply_perspective_transformation(self):
        # fovy; aspect; n; f
        # n and f from smalest bzw biggest z in vertices?
        pass

    def apply_screen_transformation(self):
        pass
