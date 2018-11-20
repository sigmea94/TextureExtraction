class Vertex:

    def __init__(self, x, y, z):
        self.pos = [x, y, z]
        # list for direct reference to adjacent faces
        self.faces = []

    def add_face(self, face):
        self.faces.append(face)
