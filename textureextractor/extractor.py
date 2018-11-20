from PIL import Image
import json
from objparser.parser import Parser
from textureextractor.viewingpipeline import Pipeline
from textureextractor import culler


class Extractor:

    def __init__(self, obj_file, camera_file, image_file, base_file=None):
        self.scene = self.__read_obj(obj_file)
        self.camera = self.__read_camera(camera_file)
        self.image = self.__read_image(image_file)
        self.base_texture = self.__read_base(base_file)

    def extract(self):
        # backface culling (after view transformation cop is [0,0,0])
        scene = culler.cull_backfaces(self.scene, self.camera["position"])
        scene.save_to_file("out.obj")

        # use list comprehension to extract only vertex coordinates
        pipeline = Pipeline(self.camera, [v.pos for v in self.scene.vertices])
        pipeline.apply_view_transformation()
        # add transformed vertices to scene
        for i, v in enumerate(pipeline.get_vertices()):
            self.scene.vertices[i].pos = v

        # TODO: frustum culling on z
        # TODO: perspective tranformation
        pass

    @staticmethod
    def __read_obj(obj_path):
        # use obj parser
        parser = Parser(obj_path)
        scene = parser.parse()
        return scene

    @staticmethod
    def __read_camera(camera_path):
        # returns dictionary with camera parameters
        # camera parameters are:
        #   - focal length
        #   - fov
        #   - position
        #   - look_direction
        if not camera_path.endswith(".json"):
            raise ValueError("camera file should be a json file")

        with open(camera_path, 'r') as f:
            camera = json.load(f)

        # validate
        if "focal_length" not in camera:
            raise ValueError("camera parameter 'focal_length' should exist")
        elif "fov" not in camera:
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
    def __read_base(base_file):
        # check for existing uv-texture image which should be refined
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
