import numpy as np
import sys
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

        # up direction is considered given
        up = np.array([0, 1, 0])
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
        projection into cuboid [0,-1]
        see CG book Chapter 13
        """
        near, far = self.__get_best_near_and_far()

        # scale f to -1
        m_scale = np.zeros((4, 4))
        m_scale[0][0] = 1/(far * math.tan(math.radians(self.fov_h/2)))
        m_scale[1][1] = 1/(far * math.tan(math.radians(self.fov_v/2)))
        m_scale[2][2] = 1 / far
        m_scale[3][3] = 1

        # transform frustum to cuboid
        m_cub = np.zeros((4, 4))
        m_cub[0][0] = far - near
        m_cub[1][1] = far - near
        m_cub[2][2] = far
        m_cub[2][3] = near
        m_cub[3][2] = near - far

        m = np.matmul(m_cub, m_scale)

        for i, v in enumerate(self.vertices):
            self.vertices[i] = np.matmul(m, v)

    def apply_perspective_transformation2(self):
        """
        projection into cube [-1,1]
        see CG lecture
        """
        near, far = self.__get_best_near_and_far()

        width = 2 * near * math.tan(math.radians(self.fov_h/2))
        height = 2 * near * math.tan(math.radians(self.fov_v/2))
        m_pers = np.zeros((4, 4))
        m_pers[0][0] = (2*near)/width
        m_pers[1][1] = (2 * near) / height
        m_pers[2][2] = -(far + near) / (near - far)
        m_pers[2][3] = (-2*far*near) / (near - far)
        m_pers[3][2] = -1

        for i, v in enumerate(self.vertices):
            self.vertices[i] = np.matmul(m_pers, v)

    def apply_perspective_transformation3(self):
        """
        keeps z value but projects x and y between -1 and 1
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
        """tbd"""
        m_screen = np.zeros((4, 4))
        m_screen[0][0] = width/2
        m_screen[1][1] = height / 2
        m_screen[0][3] = width / 2
        m_screen[1][3] = height / 2
        m_screen[3][3] = 1

        for i, v in enumerate(self.vertices):
            self.vertices[i] = np.matmul(m_screen, v)

    def __get_best_near_and_far(self):
        smallest = sys.maxsize
        biggest = 0
        for v in self.vertices:
            if abs(v[2]) > biggest:
                biggest = abs(v[2])
            if abs(v[2]) < smallest:
                smallest = abs(v[2])
        return smallest, biggest
