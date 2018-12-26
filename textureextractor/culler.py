import sys
import math
import numpy as np


def cull_backfaces(scene, cop):
    """
    discards all faces of a scene which are back facing or barely visible from center of projection (cop)
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
        pcop = pcop / np.linalg.norm(pcop)

        normal = np.array(scene.normals[face.vn_idx])
        normal = normal / np.linalg.norm(normal)

        if np.dot(normal, pcop) >= -0.1:
            # if dot-product is >= 0 the face is back facing
            # cull faces with more than about 85 degree (cos(85) ~ 0.1) too
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
            column = buffer_pos[0]
            row = buffer_pos[1]
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

        # calculate bounding box
        max_x = max(v0[0], max(v1[0], v2[0]))
        min_x = min(v0[0], min(v1[0], v2[0]))
        max_y = max(v0[1], max(v1[1], v2[1]))
        min_y = min(v0[1], min(v1[1], v2[1]))

        # total are of the face
        total_area = __triangle_area(v0, v1, v2)

        # iterate all pixels of the bounding box
        for x in range(min_x, max_x):
            for y in range(min_y, max_y):
                p = [x, y]

                # calculate area of every sub-triangle
                w12 = __triangle_area(v0, v1, p)
                w23 = __triangle_area(v1, v2, p)
                w31 = __triangle_area(v2, v0, p)

                # calculate baryzentric coordinates from sub-triangle / total-triangle ratio
                alpha = w23 / total_area
                beta = w31 / total_area
                gamma = w12 / total_area

                if alpha >= 0 and beta >= 0 and gamma >= 0:
                    z = abs(alpha * v0[2] + beta * v1[2] + gamma * v2[2])

                    # set buffer value
                    if buffer[y][x] > z:
                        buffer[y][x] = z
    return buffer


def __triangle_area(a, b, c):
    return 0.5 * ((a[0] - c[0]) * (b[1] - c[1]) - (a[1] - c[1]) * (b[0] - c[0]))


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
            # remove w value and floor x and y
            buffer_vertices.append([math.floor(screen_pos[0]), math.floor(screen_pos[1]), screen_pos[2]])

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
