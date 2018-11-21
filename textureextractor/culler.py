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


def cull_faces_behind_camera(scene):
    faces_to_discard = []
    for face in scene.faces:
        is_behind = True
        for v in face.vertices:
            if v.pos[2] < 0:
                # in front of camera
                is_behind = False
        if is_behind:
            __remove_face_from_vertices(scene, face)
            faces_to_discard.append(face)
    for f in faces_to_discard:
        scene.faces.remove(f)


def cull_frustum(scene, fov_h, fov_v):
    """cull on frustum !before! perspective projection"""
    faces_to_discard = []
    for face in scene.faces:
        is_outside = True
        tan_h = math.tan(math.radians(fov_h/2))
        tan_v = math.tan(math.radians(fov_v/2))
        for v in face.vertices:
            x = v.pos[0]
            y = v.pos[1]
            z = v.pos[2]
            max_x = tan_h * z
            max_y = tan_v * z
            if -max_x < x < max_x and -max_y < y < max_y:
                is_outside = False
        if is_outside:
            __remove_face_from_vertices(scene, face)
            faces_to_discard.append(face)
    for f in faces_to_discard:
        scene.faces.remove(f)


def __remove_face_from_vertices(scene, face):
    for v in face.vertices:
        # remove face reference from vertex
        v.faces.remove(face)
        if len(v.faces) is 0:
            # if there are no more faces associated with the vertex: delete vertex
            scene.vertices.remove(v)
