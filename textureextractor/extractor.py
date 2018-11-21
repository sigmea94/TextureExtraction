import json
import math

from PIL import Image

from objparser.parser import Parser
from textureextractor.viewingpipeline import Pipeline
from textureextractor import culler


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
         ...
        """

        # backface culling with camera as cop
        culler.cull_backfaces(self.scene, self.camera["position"])

        # use list comprehension to extract only vertex coordinates
        pipeline = Pipeline(self.camera, [v.pos for v in self.scene.vertices], self.scene.normals)
        pipeline.apply_view_transformation()
        pipeline.apply_to_scene(self.scene)

        # cull faces behind camera
        culler.cull_faces_behind_camera(self.scene)

        # TODO: frustum culling
        # frustum culling is done before perspective transformation to determine best near and far plane
        # normaly it would be better to do it after projection
        # TODO: perspective transformation
        # TODO: occlusion culling
        # TODO: screen projection
        # TODO: texture generation

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
          - focal length
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
        if "focal_length" not in camera:
            raise ValueError("camera parameter 'focal_length' should exist")
        elif "fov_horizontal" not in camera:
            raise ValueError("camera parameter 'fov' should exist")
        elif "position" not in camera:
            raise ValueError("camera parameter 'position' should exist")
        elif "look_direction" not in camera:
            raise ValueError("camera parameter 'look_direction' should exist")

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
    def __save_image(image, image_path):
        if not isinstance(image, Image):
            raise ValueError("only pillow image objects can be saved")
        image.save(image_path)

    @staticmethod
    def __calculate_vertical_fov(fov_h, aspect_ratio):
        fov_h_rad = math.radians(fov_h)
        fov_v = 2 * math.atan((1/aspect_ratio) * math.tan(fov_h_rad/2))
        return math.degrees(fov_v)
