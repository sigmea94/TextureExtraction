import sys
import math
import numpy as np
from textureextractor import utils


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
    # this values effect the performance: higher resolution slows down the application but increases the correctness of
    # the z buffer. Scenes with close occluding faces need a higher resolution.
    buffer_width = 256
    buffer_height = 256
    # threshold to prevent self occlusion resulting from discrete steps in depth buffer.
    # with a higher threshold the resolution can be reduced. The best threshold depends on the model (distances between
    # occluded faces)
    threshold = 0.1

    # calculate the position of each vertex on the buffer
    buffer_vertices = __calculate_buffer_pos(scene, buffer_width, buffer_height)
    # calculate the depth buffer
    buffer = __calculate_buffer(scene, buffer_vertices, buffer_width, buffer_height)

    faces_to_discard = []
    for i, face in enumerate(scene.faces):
        is_occluded = False
        for j in range(len(face.vertices)):
            # buffer_pos_idx = 3 * face_idx + vertex_idx (see __calculate_screen_pos)
            buffer_pos = buffer_vertices[i*3+j]
            column = math.floor(buffer_pos[0])
            row = math.floor(buffer_pos[1])
            if buffer[row][column] < abs(buffer_pos[2]) - threshold:
                # if there is only one vertex occluded: discard whole face
                is_occluded = True
                break
        if is_occluded:
            __remove_face_from_vertices(scene, face)
            faces_to_discard.append(face)

    for f in faces_to_discard:
        scene.faces.remove(f)


def __calculate_buffer(scene, buffer_vertices, buffer_width, buffer_height):
    """
    calculates a depth buffer for a given scene

    :param scene: scene for which the buffer should be calculated
    :param buffer_width: width of the buffer
    :param buffer_height: height of the buffer
    :return: the calculated depth buffer
    """
    # init buffer with max distance
    buffer = [[sys.maxsize for x in range(buffer_width)] for y in range(buffer_height)]

    for i in range(len(scene.faces)):
        # buffer_vertex_idx = 3 * face_idx + vertex_idx (see __calculate_screen_pos)
        v0 = buffer_vertices[3 * i]
        v1 = buffer_vertices[3 * i + 1]
        v2 = buffer_vertices[3 * i + 2]

        # calculate the best step size in alpha and beta direction
        alpha_step, beta_step = utils.calculate_baryzentric_step_size(v0, v1, v2)

        # iterate all pixel within the triangle using baryzentric interpolation
        # starting on the v1 v2 edge.
        alpha = 0
        while alpha <= 1:
            beta = 0
            while beta <= 1 - alpha:
                # alpha + beta + gamma = 1
                gamma = round(1 - alpha - beta, 5)

                # interpolate
                x = alpha * v0[0] + beta * v1[0] + gamma * v2[0]
                y = alpha * v0[1] + beta * v1[1] + gamma * v2[1]
                z = abs(alpha * v0[2] + beta * v1[2] + gamma * v2[2])

                # set buffer value
                row = math.floor(y)
                column = math.floor(x)
                if buffer[row][column] > z:
                    buffer[row][column] = z

                # next beta value
                beta = round(beta + beta_step, 5)
            # next alpha value
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


def __calculate_buffer_pos(scene, width, height):
    """
    calculates a list of buffer position of each vertex, keeps the corresponding z value
    the j-th vertex of the i-th face will be stored at index 3*i+j

    :param scene: scene for whose points the positions are to be calculated
    :param width: width of the buffer
    :param height: height of the buffer
    :return: a list of buffer positions
    """
    # projection matrix
    m_buffer = np.zeros((4, 4))
    m_buffer[0][0] = width / 2
    m_buffer[1][1] = height / 2
    m_buffer[0][3] = width / 2
    m_buffer[1][3] = height / 2
    m_buffer[2][2] = 1
    m_buffer[3][3] = 1

    buffer_vertices = []
    for face in scene.faces:
        for v in face.vertices:
            screen_pos = np.matmul(m_buffer, np.append(np.array(v.pos), np.array([1])))
            # remove w value
            buffer_vertices.append(np.delete(screen_pos, 3).tolist())

    return buffer_vertices


def __remove_face_from_vertices(scene, face):
    """
    removes a face reference from corresponding vertices.
    deletes the vertex if there are no more associated faces to the vertex

    :param scene: scene the face belongs to
    :param face: face which should be removed
    """
    for v in face.vertices:
        # remove face reference from vertex
        v.faces.remove(face)
        if len(v.faces) is 0:
            # if there are no more faces associated with the vertex: delete vertex
            scene.vertices.remove(v)
