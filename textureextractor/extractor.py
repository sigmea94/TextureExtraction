from PIL import Image
import json
from extendedobjparser.parser import Parser


class Extractor:

    def __init__(self, obj_file, camera_file, image_file, base_file=None):
        self.obj_file = self.__read_obj(obj_file)
        self.camera_file = self.__read_camera(camera_file)
        self.image_file = self.__read_image(image_file)
        self.base_file = self.__read_base(base_file)

    def extract(self):
        # Todo: extract
        # Todo: save image
        pass

    @staticmethod
    def __read_obj(obj_path):
        # parse file, check file is obj file
        if not obj_path.endswith(".obj"):
            raise ValueError("model file should be an obj file")
        # use extended obj parser
        parser = Parser(obj_path)
        obj = parser.parse()
        # return scene (list of meshes)
        return obj

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
