import math


def calculate_baryzentric_step_size(v1, v2, v3):
    """
    Calculates the optimal steps size for baryzentric interpolation of a triangle defined by vertices v1 v2 v3.
    The calculated step size ensures that one step is performed for each pixel within the triangle.

    :param v1: first vertex
    :param v2: second vertex
    :param v3: third vertex
    :return: step size for alpha and beta for baryzentric interpolation
    """
    # calculate the best step size in alpha and beta direction
    # use median line for alpha
    middle_x = 0.5 * v2[0] + 0.5 * v3[0]
    middle_y = 0.5 * v2[1] + 0.5 * v3[1]

    # alpha distance in pixel
    alpha_distance = round(math.sqrt((v1[0] - middle_x) ** 2 + (v1[1] - middle_y) ** 2))

    # or take biggest_distance?
    # dist12 = math.sqrt((v1[0] - v2[0]) ** 2 + (v1[1] - v2[1]) ** 2)
    # dist13 = math.sqrt((v1[0] - v3[0]) ** 2 + (v1[1] - v3[1]) ** 2)
    # alpha_distance = dist12 if dist12 > dist13 else dist13

    # beta distance in pixel
    beta_distance = round(math.sqrt((v2[0] - v3[0]) ** 2 + (v2[1] - v3[1]) ** 2))

    # for every pixel one step should be taken
    # round to 5 decimal digits to prevent float incorrectness
    alpha_step = round(1 / alpha_distance, 5)
    beta_step = round(1 / beta_distance, 5)

    return alpha_step, beta_step

