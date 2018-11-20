import numpy as np


def cull_backfaces(scene, cop):
    cop = np.array(cop)
    faces_to_discard = []
    for face in scene.faces:
        p = np.array(face.vertices[0].pos)
        normal = np.array(scene.normals[face.vn_idx])
        pcop = p - cop
        dot = np.dot(normal, pcop)
        if dot > 0:
            for v in face.vertices:
                v.faces.remove(face)
                if len(v.faces) is 0:
                    # delete vertex
                    scene.vertices.remove(v)
            faces_to_discard.append(face)
    for f in faces_to_discard:
        scene.faces.remove(f)
    return scene
