import json
import math

from PIL import Image
import numpy as np

from objparser.parser import Parser
from textureextractor.viewingpipeline import Pipeline
from textureextractor import culler
import config


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
        # convert images to arrays for better performance
        im = np.array(self.image)
        texture = np.array(self.base_texture)

        # get size of images only once to increase performance
        texture_width = texture.shape[1]
        texture_height = texture.shape[0]

        for f in self.scene.faces:
            texture_pos = []
            image_pos = []

            # calculate vertices on texture map and corresponding vertices on image
            for i in range(len(f.vertices)):
                # texture coordinates are specified as a percentage of the total image size
                vt = self.scene.texture_coords[f.vt_indices[i]]
                x = texture_width * vt[0]
                # texture coordinate is given from lower left corner but image coordinates start on upper left corner
                y = texture_height * (1-vt[1])

                texture_pos.append([x, y])

                # get the corresponding image vertex
                pos = f.vertices[i].pos
                image_pos.append([pos[0], pos[1]])

            # a face is build of three vertices (resulting in three texture vertices (vt) and three image vertices (v))
            vt1 = texture_pos[0]
            vt2 = texture_pos[1]
            vt3 = texture_pos[2]
            v1 = image_pos[0]
            v2 = image_pos[1]
            v3 = image_pos[2]

            # calculate bounding box
            max_x = math.ceil(max(vt1[0], max(vt2[0], vt3[0])))
            min_x = math.floor(min(vt1[0], min(vt2[0], vt3[0])))
            max_y = math.ceil(max(vt1[1], max(vt2[1], vt3[1])))
            min_y = math.floor(min(vt1[1], min(vt2[1], vt3[1])))

            # total are of the face
            total_area = self.__triangle_area(vt1, vt2, vt3)
            if total_area == 0.0:
                continue

            # iterate all pixels of the bounding box
            for x in range(min_x, max_x):
                for y in range(min_y, max_y):
                    # calculate area of every sub-triangle, take center of pixel
                    w12 = self.__triangle_area(vt1, vt2, [x+0.5, y+0.5])
                    w23 = self.__triangle_area(vt2, vt3, [x+0.5, y+0.5])
                    w31 = self.__triangle_area(vt3, vt1, [x+0.5, y+0.5])

                    # calculate baryzentric coordinates from sub-triangle / total-triangle ratio
                    alpha = w23 / total_area
                    beta = w31 / total_area
                    gamma = w12 / total_area

                    if alpha >= 0 and beta >= 0 and gamma >= 0:
                        # point is inside triangle

                        # a texture map can be seen as a torus
                        # This is because coordinates larger than the texture image begin left (x) or top (y) again.
                        # Therefore, the corresponding texture coordinates within the texture image size are calculated.
                        x_texture = x
                        y_texture = y
                        while x_texture >= texture_width:
                            x_texture -= texture_width
                        while y_texture >= texture_height:
                            y_texture -= texture_height

                        # interpolate image position
                        x_image = math.floor(alpha * v1[0] + beta * v2[0] + gamma * v3[0])
                        y_image = math.floor(alpha * v1[1] + beta * v2[1] + gamma * v3[1])

                        # copy pixel [y_image, x_image] to [y_texture, x_texture]
                        pixel = im[y_image][x_image]
                        texture[y_texture][x_texture] = pixel

        self.base_texture = Image.fromarray(texture)

    @staticmethod
    def __triangle_area(a, b, c):
        return 0.5 * ((a[0] - c[0]) * (b[1] - c[1]) - (a[1] - c[1]) * (b[0] - c[0]))

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
        if config.quality_mode:
            mode = 'RGBA'
        else:
            mode = 'RGB'
        # open image and return pixel accessible format
        img = Image.open(image_path, mode='r').convert(mode)
        return img

    @staticmethod
    def __read_base(base_file=None):
        """
        opens given image or creates new one if it isn't given

        :param base_file: path to uv-texture file which should be refined (optional)
        :return: texture image
        """
        if config.quality_mode:
            mode = 'RGBA'
        else:
            mode = 'RGB'
        # create a new one if there is no existing
        if base_file is not None:
            base = Image.open(base_file, mode='r')
        else:
            base = Image.new(mode, (config.texture_width, config.texture_height))
        return base

    @staticmethod
    def __calculate_vertical_fov(fov_h, aspect_ratio):
        fov_h_rad = math.radians(fov_h)
        fov_v = 2 * math.atan((1/aspect_ratio) * math.tan(fov_h_rad/2))
        return math.degrees(fov_v)
