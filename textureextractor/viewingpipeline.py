import numpy as np
import math


class Pipeline:

    def __init__(self, camera, vertices, normals):
        """
        init the pipeline by setting vertices, normals, camera coos axis and camera position in the scene coos
        camera coos axis are: u, v, w

        :param camera: camera from which the scene is viewed
        :param vertices: initial vertices
        :param normals: initial normals
        """
        self.fov_h = camera["fov_horizontal"]
        self.fov_v = camera["fov_vertical"]

        self.vertices = []
        self.set_vertices(vertices)
        self.normals = []
        self.set_normals(normals)

        look = np.array(camera["look_direction"])
        self.w = -look / np.linalg.norm(look)

        up = camera["up_direction"]
        cross = np.cross(up, self.w)
        self.u = cross / np.linalg.norm(cross)
        self.v = np.cross(self.w, self.u)
        self.camera_pos = np.array(camera["position"])

    def set_vertices(self, vertices):
        """
        homogenize vertices, convert to numpy array and add to list

        :param vertices: list of vertices
        """
        self.vertices = []
        for v in vertices:
            self.vertices.append(np.append(np.array(v), np.array([1])))

    def get_vertices(self):
        """
        :return: normalized vertices as list
        """
        res = []
        for v in self.vertices:
            # divide by w value
            vertex = [a/v[3] for a in v]
            res.append(np.delete(vertex, 3).tolist())
        return res

    def set_normals(self, normals):
        """
        homogenize normals, convert to numpy array and add to list

        :param normals: list of normals
        """
        self.normals = []
        for n in normals:
            self.normals.append(np.append(np.array(n), np.array([1])))

    def get_normals(self):
        """
        :return: normals as list
        """
        res = []
        for n in self.normals:
            res.append(np.delete(n, 3).tolist())
        return res

    def apply_to_scene(self, scene):
        """
        add transformed vertices and normals to scene

        :param scene: scene to which vertices and normals should be applied
        """
        for i, v in enumerate(self.get_vertices()):
            scene.vertices[i].pos = v
        scene.normals = self.get_normals()

    def apply_view_transformation(self):
        """
        applies the view transformation to vertices and normals
        the view transformation sets the camera as origin of the new coos specified by u, v and w

        t_an translates all vertices in order to set the camera as new origin
        m_an rotates all vertices and normals in order to orientate the scene by the new axis
        both transformations can be combined in a single matrix view_mat
        """
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

        # only the rotation needs to be applied to the normals
        for i, n in enumerate(self.normals):
            self.normals[i] = np.matmul(m_an, n)

    def apply_perspective_transformation(self):
        """
        transforms view frustum into cuboid.
        the x and y values are limited between -1 and 1

        Note: this transformation keeps the z value for easier occlusion culling
        """
        tan_h = math.tan(math.radians(self.fov_h/2))
        tan_v = math.tan(math.radians(self.fov_v/2))
        for i, v in enumerate(self.vertices):
            z = v[2]
            if z == 0:
                x = 0
                y = 0
            else:
                # x / max_x
                x = v[0] / (tan_h * abs(z))
                # y / max_y
                y = v[1] / (tan_v * abs(z))
            self.vertices[i] = np.array([x, y, z, v[3]])

    def apply_screen_transformation(self, width, height):
        """
        transforms the scene into the 2D screen plane

        :param width: width of the screen/image in pixel
        :param height: height of the screen/image in pixel
        """
        m_screen = np.zeros((4, 4))
        m_screen[0][0] = width / 2
        m_screen[1][1] = - height / 2
        m_screen[0][3] = width / 2
        m_screen[1][3] = height / 2
        m_screen[3][3] = 1

        for i, v in enumerate(self.vertices):
            self.vertices[i] = np.matmul(m_screen, v)
