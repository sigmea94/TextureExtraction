import sys
import time
from textureextractor.extractor import Extractor


def main():
    if "--help" in sys.argv or (len(sys.argv) != 4 and len(sys.argv) != 5):
        # args are path to obj file (argv[1]), camera parameters in json file format (argv[2]),
        # the image file from which the texture should be extracted (argv[3])
        # and an optional base uv-texture which should be refined (argv[4])
        print("Usage:")
        print(sys.argv[0] + " path_to_obj_file path_to_camera_json path_to_image [path_to_base_image]")
        return

    scene = sys.argv[1]
    camera = sys.argv[2]
    image = sys.argv[3]
    if len(sys.argv) == 5:
        base = sys.argv[4]
    else:
        base = None

    extractor = Extractor(scene, camera, image, base)
    extractor.extract()


if __name__ == "__main__":
    start_time = time.time()
    main()
    print("--- %s seconds ---" % (time.time() - start_time))
