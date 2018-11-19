from PIL import Image
import json
from extendedobjparser.parser import Parser


class Extractor:

    def __init__(self, obj_file, camera_file, image_file, base_file=None):
        self.obj_file = read_obj(obj_file)
        self.camera_file = read_camera(camera_file)
        self.image_file = read_image(image_file)
        self.base_file = read_base(base_file)

    def extract(self):
        # Todo: extract
        # Todo: save image
        pass


def read_obj(obj_path):
    # parse file, check file is obj file
    if not obj_path.endswith(".obj"):
        raise ValueError("model file should be an obj file")
    # use extended obj parser
    parser = Parser(obj_path)
    obj = parser.parse()
    # return scene (list of meshes)
    return obj


def read_camera(camera_path):
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


def read_image(image_path):
    # open image and return pixel accessible format
    img = Image.open(image_path, mode='r')
    return img


def read_base(base_file):
    # check for existing uv-texture image which should be refined
    # create a new one if there is no existing
    if base_file is not None:
        base = read_image(base_file)
    else:
        base = Image.new('RGB', (1024, 1024))
    return base


def save_image(image, image_path):
    if not isinstance(image, Image):
        raise ValueError("only pillow image objects can be saved")
    image.save(image_path)
