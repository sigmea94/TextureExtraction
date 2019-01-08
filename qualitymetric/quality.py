import time
import sys
from PIL import Image, ImageFilter
import math
from skimage import color
import numpy as np

blur = True
fault_intensity = False


def main():
    if len(sys.argv) is 3:
        ground_truth_path = sys.argv[1]
        texture_path = sys.argv[2]

        ground_truth = Image.open(ground_truth_path).convert('RGBA')
        rgba_texture = Image.open(texture_path)
        if rgba_texture.mode is not 'RGBA':
            print("texture should be in RGBA mode")
            return
        if rgba_texture.size != ground_truth.size:
            print("Images cant be compared")
            return

        if blur:
            texture = Image.alpha_composite(ground_truth, rgba_texture)

            # Blur images
            texture = texture.filter(ImageFilter.GaussianBlur(2))
            ground_truth = ground_truth.filter(ImageFilter.GaussianBlur(2))
        else:
            texture = rgba_texture

        rgba_texture = np.array(rgba_texture)

        # convert to Lab color
        texture = color.rgb2lab(color.rgba2rgb(texture))
        ground_truth = color.rgb2lab(color.rgba2rgb(ground_truth))

        visual_quality_image = Image.new('RGBA', (rgba_texture.shape[1], rgba_texture.shape[0]))
        visual_quality_pixels = visual_quality_image.load()

        total_distance = 0
        total_ratio = 0
        pixels = 0
        max_distance = math.sqrt(100 ** 2 + 256 ** 2 + 256 ** 2)

        for y in range(rgba_texture.shape[0]):
            for x in range(rgba_texture.shape[1]):
                alpha = rgba_texture[y][x][3]
                if alpha == 0:
                    continue
                ground_truth_pixel = ground_truth[y][x]
                texture_pixel = texture[y][x]

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
                if fault_intensity:
                    value = math.floor(difference_ratio**0.5 * 255)
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
