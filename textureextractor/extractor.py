import json
import math

from PIL import Image
import numpy as np

from objparser.parser import Parser
from textureextractor.viewingpipeline import Pipeline
from textureextractor import culler
from textureextractor import utils


class Extractor:

    def __init__(self, obj_file, camera_file, image_file, base_file=None):
        self.scene = self.__read_obj(obj_file)
        self.camera = self.__read_camera(camera_file)
        self.image = self.__read_image(image_file)
        self.base_texture = self.__read_base(base_file)

        # take image aspect ratio as camera's aspect ratio
        self.camera["aspect_ratio"] = self.image.width / self.image.height
        # calculate vertical fov from horizontal fov and aspect ratio
        self.camera["fov_vertical"] = self.__calculate_vertical_fov(
            self.camera["fov_horizontal"], self.camera["aspect_ratio"])

    def extract(self):
        """
        extract a texture
        steps:
         1. cull backfaces
         2. apply view transformation to scene
         3. perspective transformation
         4. cull faces outside the view frustum
         5. occlusion culling
         6. screen transformation
         7. copy pixels
        """

        # backface culling with camera as cop
        culler.cull_backfaces(self.scene, self.camera["position"])

        # use list comprehension to extract only vertex coordinates
        pipeline = Pipeline(self.camera, [v.pos for v in self.scene.vertices], self.scene.normals)
        pipeline.apply_view_transformation()

        # perspective transfomation
        pipeline.apply_perspective_transformation()

        # frustum culling
        pipeline.apply_to_scene(self.scene)
        culler.cull_frustum(self.scene)

        # occlusion culling
        culler.cull_occluded(self.scene)

        # screen transformation
        pipeline.set_vertices([v.pos for v in self.scene.vertices])
        pipeline.apply_screen_transformation(self.image.width, self.image.height)
        pipeline.apply_to_scene(self.scene)

        # copy pixels from image to texture image
        self.__copy_pixel()

        # save texture in file
        self.base_texture.save("texture.png")

    def __copy_pixel(self):
        # TODO parallelize on gpu
        for f in self.scene.faces:
            texture_pos = []
            image_pos = []

            # calculate vertices on texture map and corresponding vertices on image
            for i in range(len(f.vertices)):
                # texture coordinates are specified as a percentage of the total image size
                vt = self.scene.texture_coords[f.vt_indices[i]]
                x = math.floor(self.base_texture.width * vt[0])
                y = math.floor(self.base_texture.height * vt[1])
                # texture coordinate is given from lower left corner but image coordinates start on upper left corner
                y = self.base_texture.height - y
                texture_pos.append([x, y])

                # get the corresponding image vertex
                image_pos.append(f.vertices[i].pos)

            # a face is build of three vertices (resulting in three texture vertices (vt) and three image vertices (v))
            vt1 = texture_pos[0]
            vt2 = texture_pos[1]
            vt3 = texture_pos[2]
            v1 = image_pos[0]
            v2 = image_pos[1]
            v3 = image_pos[2]

            # calculate the best step size in alpha and beta direction
            alpha_step, beta_step = utils.calculate_baryzentric_step_size(vt1, vt2, vt3)

            # iterate all pixel within the triangle using baryzentric interpolation
            # starting on the v2 v3 edge
            alpha = 0
            while alpha <= 1:
                beta = 0
                while beta <= 1 - alpha:
                    gamma = round(1 - alpha - beta, 5)

                    # interpolate texture position
                    x_texture = math.floor(alpha * vt1[0] + beta * vt2[0] + gamma * vt3[0])
                    y_texture = math.floor(alpha * vt1[1] + beta * vt2[1] + gamma * vt3[1])

                    # a texture map can be seen as a torus
                    # This is because coordinates larger than the texture image begin left (x) or top (y) again.
                    # Therefore, the corresponding texture coordinates within the texture image size are calculated.
                    while x_texture >= self.base_texture.width:
                        x_texture -= self.base_texture.width
                    while y_texture >= self.base_texture.height:
                        y_texture -= self.base_texture.height

                    # interpolate image position
                    x_image = math.floor(alpha * v1[0] + beta * v2[0] + gamma * v3[0])
                    y_image = math.floor(alpha * v1[1] + beta * v2[1] + gamma * v3[1])
                    # model y axis is up but image y axis is down
                    y_image = self.image.height - y_image

                    # copy pixel [y_image, x_image] to [y_texture, x_texture]
                    pixel = self.image.getpixel((x_image, y_image))
                    self.base_texture.putpixel((x_texture, y_texture), pixel)

                    beta = round(beta + beta_step, 5)
                alpha = round(alpha + alpha_step, 5)

    @staticmethod
    def __read_obj(obj_path):
        # use obj parser
        parser = Parser(obj_path)
        scene = parser.parse()
        return scene

    @staticmethod
    def __read_camera(camera_path):
        """
        camera parameters are:
          - horizontal fov
          - position
          - look_direction
        :param camera_path: path to json file which specifies the camera
        :return: dictionary with camera parameters
        """
        if not camera_path.endswith(".json"):
            raise ValueError("camera file should be a json file")

        with open(camera_path, 'r') as f:
            camera = json.load(f)

        # validate
        if "fov_horizontal" not in camera:
            raise ValueError("camera parameter 'fov' should exist")
        elif "position" not in camera:
            raise ValueError("camera parameter 'position' should exist")
        elif "look_direction" not in camera:
            raise ValueError("camera parameter 'look_direction' should exist")
        elif "up_direction" not in camera:
            raise ValueError("camera parameter 'up_direction' should exist")

        if np.array_equal(np.cross(camera["look_direction"], camera["up_direction"]), [0, 0, 0]):
            raise ValueError("look_direction and up_direction must not be parallel")

        return camera

    @staticmethod
    def __read_image(image_path):
        # open image and return pixel accessible format
        img = Image.open(image_path, mode='r')
        return img

    @staticmethod
    def __read_base(base_file=None):
        """
        opens given image or creates new one if it isn't given

        :param base_file: path to uv-texture file which should be refined (optional)
        :return: texture image
        """
        # create a new one if there is no existing
        if base_file is not None:
            base = Image.open(base_file, mode='r')
        else:
            base = Image.new('RGB', (1024, 1024))
        return base

    @staticmethod
    def __calculate_vertical_fov(fov_h, aspect_ratio):
        fov_h_rad = math.radians(fov_h)
        fov_v = 2 * math.atan((1/aspect_ratio) * math.tan(fov_h_rad/2))
        return math.degrees(fov_v)
