import time
import sys
from PIL import Image
import math
from skimage import io, color


def main():
    if len(sys.argv) is 3:
        ground_truth_path = sys.argv[1]
        texture_path = sys.argv[2]

        ground_truth = io.imread(ground_truth_path)
        if ground_truth.shape[2] == 4:
            ground_truth = color.rgba2rgb(ground_truth)
        ground_truth = color.rgb2lab(ground_truth)

        texture = io.imread(texture_path)
        if texture.shape[2] != 4:
            print("texture should be rgba Format")
            return

        texture_lab = color.rgb2lab(color.rgba2rgb(texture))

        if texture.shape[0] != ground_truth.shape[0] or texture.shape[1] != ground_truth.shape[1]:
            print("Images cant be compared")
            return

        visual_quality_image = Image.new('RGBA', (texture.shape[1], texture.shape[0]))
        visual_quality_pixels = visual_quality_image.load()

        total_distance = 0
        total_ratio = 0
        pixels = 0

        max_distance = math.sqrt(100 ** 2 + 256 ** 2 + 256 ** 2)

        for y in range(texture.shape[0]):
            for x in range(texture.shape[1]):
                alpha = texture[y][x][3]
                if alpha == 0:
                    continue
                ground_truth_pixel = ground_truth[y][x]
                texture_pixel = texture_lab[y][x]

                r_distance = abs(texture_pixel[0] - ground_truth_pixel[0])
                g_distance = abs(texture_pixel[1] - ground_truth_pixel[1])
                b_distance = abs(texture_pixel[2] - ground_truth_pixel[2])

                distance = math.sqrt(r_distance ** 2 + g_distance ** 2 + b_distance ** 2)
                difference_ratio = distance/max_distance

                if distance > 18.78:
                    # min 5% difference color red
                    value = 255
                else:
                    value = 0
                visual_quality_pixels[x, y] = (value, 0, 0, 255)

                total_ratio += difference_ratio
                total_distance += distance
                pixels += 1

        print("Total Distance: " + str(total_distance))
        print("Average Distance: " + str(total_distance/pixels))
        print("Average Ratio: " + str(100 * total_ratio/pixels) + "%")
        visual_quality_image.save("visual_quality.png")

    else:
        print("please provide ground truth and texture")


if __name__ == "__main__":
    start_time = time.time()
    main()
    print("--- %s seconds ---" % (time.time() - start_time))
