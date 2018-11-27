import sys
import math
import numpy as np


def cull_backfaces(scene, cop):
    """
    discards all faces of a scene which are back facing from center of projection (cop)
    also deletes vertices without corresponding faces
    normals and texture coords won't be deleted

    :param scene: scene from which backfaces should be removed
    :param cop: center of projection
    """
    faces_to_discard = []
    for face in scene.faces:
        # take first vertex as point on mesh
        p = np.array(face.vertices[0].pos)
        # pcop: vector from cop to point p on triangle
        pcop = p - np.array(cop)

        normal = np.array(scene.normals[face.vn_idx])
        if np.dot(normal, pcop) >= 0:
            # if dot-product is >= 0 the face is back facing
            __remove_face_from_vertices(scene, face)
            faces_to_discard.append(face)
    for f in faces_to_discard:
        scene.faces.remove(f)


def cull_frustum(scene):
    """
    cull on frustum after perspective projection
    x and y are  between -1 and 1
    z is less than 0

    :param scene: scene from which faces outside the frustum should be removed
    """
    faces_to_discard = []
    for face in scene.faces:
        is_outside = False
        for v in face.vertices:
            x = v.pos[0]
            y = v.pos[1]
            z = v.pos[2]
            if x < -1 or x > 1 or y < -1 or y > 1 or z >= 0:
                # if there is only one vertex outside: discard whole face
                is_outside = True
                break
        if is_outside:
            __remove_face_from_vertices(scene, face)
            faces_to_discard.append(face)
    for f in faces_to_discard:
        scene.faces.remove(f)


def cull_occluded(scene):
    """
    removes occluded faces via z-buffer

    :param scene: scene from which occluded faces should be removed
    """
    # project every face to z buffer compare and discard if z value is larger

    # this values effect the performance: higher resolution slows down the application but increases the correctness of
    # the z buffer. Close occlusion needs a higher resolution.
    # with a higher threshold the resolution can be reduced. The threshold depends on the model (distances between
    # occluded faces)
    buffer_width = 512
    buffer_height = 512
    # threshold to prevent self occlusion resulting from discrete steps in depth buffer.
    threshold = 0.5

    buffer = __calculate_buffer(scene, buffer_width, buffer_height)

    # now start occlusion culling
    m_screen = np.zeros((4, 4))
    m_screen[0][0] = buffer_width / 2
    m_screen[1][1] = buffer_height / 2
    m_screen[0][3] = buffer_width / 2
    m_screen[1][3] = buffer_height / 2
    m_screen[3][3] = 1

    faces_to_discard = []
    for face in scene.faces:
        is_occluded = False
        for v in face.vertices:
            screen_pos = np.matmul(m_screen, np.append(np.array(v.pos), np.array([1])))
            x = math.floor(screen_pos[0])
            y = math.floor(screen_pos[1])
            if buffer[y][x] < abs(v.pos[2]) - threshold:
                # if there is only one vertex occluded: discard whole face
                is_occluded = True
                break
        if is_occluded:
            __remove_face_from_vertices(scene, face)
            faces_to_discard.append(face)
    for f in faces_to_discard:
        scene.faces.remove(f)


def __calculate_buffer(scene, buffer_width, buffer_height):
    """
    calculates a depth buffer for a given scene

    :param scene:
    :param buffer_width:
    :param buffer_height:
    :return:
    """
    # init buffer with max distance
    buffer = [[sys.maxsize for x in range(buffer_width)] for y in range(buffer_height)]

    m_screen = np.zeros((4, 4))
    m_screen[0][0] = buffer_width / 2
    m_screen[1][1] = buffer_height / 2
    m_screen[0][3] = buffer_width / 2
    m_screen[1][3] = buffer_height / 2
    m_screen[3][3] = 1

    for f in scene.faces:
        vertices_on_buffer = []
        for v in f.vertices:
            buffer_pos = np.matmul(m_screen, np.append(np.array(v.pos), np.array([1])))
            x = buffer_pos[0]
            y = buffer_pos[1]
            z = abs(v.pos[2])
            vertices_on_buffer.append([x, y, z])

        # use median line
        middle_x = 0.5 * vertices_on_buffer[1][0] + 0.5 * vertices_on_buffer[2][0]
        middle_y = 0.5 * vertices_on_buffer[1][1] + 0.5 * vertices_on_buffer[2][1]

        alpha_distance = math.sqrt(
            (vertices_on_buffer[0][0] - middle_x) ** 2 + (vertices_on_buffer[0][1] - middle_y) ** 2
        )

        # or take biggest_distance?
        # dist12 = math.sqrt((vertices_on_buffer[0][0] - vertices_on_buffer[1][0]) ** 2
        #                    + (vertices_on_buffer[0][1] - vertices_on_buffer[1][1]) ** 2)
        # dist13 = math.sqrt((vertices_on_buffer[0][0] - vertices_on_buffer[2][0]) ** 2
        #                    + (vertices_on_buffer[0][1] - vertices_on_buffer[2][1]) ** 2)
        # alpha_distance = dist12 if dist12 > dist13 else dist13

        # beta distance
        beta_distance = math.sqrt(
            (vertices_on_buffer[1][0] - vertices_on_buffer[2][0]) ** 2
            + (vertices_on_buffer[1][1] - vertices_on_buffer[2][1]) ** 2
        )
        alpha_step = round(1 / round(alpha_distance), 5)
        beta_step = round(1 / round(beta_distance), 5)

        alpha = 0
        while alpha <= 1:
            beta = 0
            while beta <= 1 - alpha:
                gamma = round(1 - alpha - beta, 5)
                x = alpha * vertices_on_buffer[0][0] + beta * vertices_on_buffer[1][0] \
                    + gamma * vertices_on_buffer[2][0]
                y = alpha * vertices_on_buffer[0][1] + beta * vertices_on_buffer[1][1] \
                    + gamma * vertices_on_buffer[2][1]
                z = alpha * vertices_on_buffer[0][2] + beta * vertices_on_buffer[1][2] \
                    + gamma * vertices_on_buffer[2][2]

                row = math.floor(y)
                column = math.floor(x)
                if buffer[row][column] > z:
                    buffer[row][column] = z

                beta = round(beta + beta_step, 5)
            alpha = round(alpha + alpha_step, 5)

    # write buffer in file for debugging purposes
    # f = open("buffer.txt", 'w')
    # for row in buffer:
    #     for value in row:
    #         if value is sys.maxsize:
    #             value = 0
    #         f.write('{:.2f} '.format(value))
    #     f.write("\n")
    return buffer


def __remove_face_from_vertices(scene, face):
    for v in face.vertices:
        # remove face reference from vertex
        v.faces.remove(face)
        if len(v.faces) is 0:
            # if there are no more faces associated with the vertex: delete vertex
            scene.vertices.remove(v)
