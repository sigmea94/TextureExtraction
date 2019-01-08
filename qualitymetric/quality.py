import time
import sys
from PIL import Image
import math


def main():
    if len(sys.argv) is 3:
        path1 = sys.argv[1]
        path2 = sys.argv[2]
        ground_truth = Image.open(path1, mode='r').convert('RGB')
        texture = Image.open(path2, mode='r').convert('RGBA')
        if texture.size != ground_truth.size:
            print("Images cant be compared")
            return

        visual_quality = Image.new('RGBA', (texture.width, texture.height))
        pixels_123 = visual_quality.load()

        total_distance = 0
        pixels = 0

        max_distance = math.sqrt(255 ** 2 + 255 ** 2 + 255 ** 2)

        for y in range(texture.height):
            for x in range(texture.width):
                texture_pixel = texture.getpixel((x, y))
                if texture_pixel[3] == 0:
                    continue
                truth_pixel = ground_truth.getpixel((x, y))

                r_distance = abs(texture_pixel[0] - truth_pixel[0])
                g_distance = abs(texture_pixel[1] - truth_pixel[1])
                b_distance = abs(texture_pixel[2] - truth_pixel[2])

                distance = math.sqrt(r_distance ** 2 + g_distance ** 2 + b_distance ** 2)
                ratio = distance/max_distance

                value = math.floor(ratio*255)
                pixels_123[x, y] = (value, 0, 0, 255)

                total_distance += distance
                pixels += 1

        print("Total Distance: " + str(total_distance))
        print("Average Distance: " + str(total_distance/pixels))
        visual_quality.save("visual_quality.png")

    else:
        print("please provide ground truth and texture")


if __name__ == "__main__":
    start_time = time.time()
    main()
    print("--- %s seconds ---" % (time.time() - start_time))
