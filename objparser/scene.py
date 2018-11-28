class Scene:
    """
    class represents a 3D-Scene build of triangular meshes
    it contains of:
     a list of vertices
     a list of texture coordinates
     a list of normals
     a list of faces
    """

    def __init__(self, v, vt, vn, f):
        self.vertices = v
        self.texture_coords = vt
        self.normals = vn
        self.faces = f

    def save_to_file(self, file_path):
        """method to save scene as a obj file"""
        if not file_path.endswith(".obj"):
            raise ValueError("scene should be save as an obj file")
        f = open(file_path, 'w')

        # save vertices
        for v in self.vertices:
            x = v.pos[0]
            y = v.pos[1]
            z = v.pos[2]
            f.write("v " + str(x) + " " + str(y) + " " + str(z) + "\n")

        # save texture
        for vt in self.texture_coords:
            f.write("vt " + str(vt[0]) + " " + str(vt[1]) + "\n")

        # save normals
        for vn in self.normals:
            f.write("vn " + str(vn[0]) + " " + str(vn[1]) + " " + str(vn[2]) + "\n")

        # save faces
        for face in self.faces:
            face_line = "f "
            for i in range(3):
                v_idx = self.vertices.index(face.vertices[i])
                face_line += str(v_idx + 1) + "/" + str(face.vt_indices[i] + 1) + "/" + str(face.vn_idx + 1) + " "
            f.write(face_line + "\n")

        f.close()
