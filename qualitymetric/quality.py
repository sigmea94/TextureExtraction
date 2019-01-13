import time
import sys
from PIL import Image, ImageFilter
import math
from skimage import color
import numpy as np
import config


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

        if config.quality_blur:
            texture = Image.alpha_composite(ground_truth, rgba_texture)

            # Blur images
            texture = texture.filter(ImageFilter.GaussianBlur(config.quality_blur_rate))
            ground_truth = ground_truth.filter(ImageFilter.GaussianBlur(config.quality_blur_rate))
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
        total_pixels = 0
        bad_pixels = 0
        max_distance = math.sqrt(100 ** 2 + 255 ** 2 + 255 ** 2)

        distance_array = color.deltaE_cie76(texture, ground_truth)

        for y in range(rgba_texture.shape[0]):
            for x in range(rgba_texture.shape[1]):
                alpha = rgba_texture[y][x][3]
                if alpha == 0:
                    continue

                distance = distance_array[y][x]
                difference_ratio = distance/max_distance

                if distance > 0.05 * max_distance:
                    # min 2.5% difference color red
                    value = 255
                    bad_pixels += 1
                else:
                    value = 0
                if config.quality_show_fault_intensity:
                    value = math.floor(difference_ratio**0.5 * 255)
                visual_quality_pixels[x, y] = (value, 0, 0, 255)

                total_ratio += difference_ratio
                total_distance += distance
                total_pixels += 1

        print("Total Distance: " + str(total_distance))
        print("Total Pixels: " + str(total_pixels))
        print("Average Distance: " + str(total_distance/total_pixels))
        print("Average Ratio: " + str(100 * total_ratio/total_pixels) + "%")
        print("Bad Pixels Ratio: " + str(100 * bad_pixels/total_pixels) + "%")

        visual_quality_image.save("visual_quality.png")

    else:
        print("please provide ground truth and texture")


if __name__ == "__main__":
    start_time = time.time()
    main()
    print("--- %s seconds ---" % (time.time() - start_time))
