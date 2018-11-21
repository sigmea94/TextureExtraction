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
            for v in face.vertices:
                # remove face reference from vertex
                v.faces.remove(face)
                if len(v.faces) is 0:
                    # if there are no more faces associated with the vertex: delete vertex
                    scene.vertices.remove(v)
            faces_to_discard.append(face)
    for f in faces_to_discard:
        scene.faces.remove(f)
