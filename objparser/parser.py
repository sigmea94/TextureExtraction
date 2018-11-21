from objparser.vertex import Vertex
from objparser.face import Face
from objparser.scene import Scene


class Parser:

    def __init__(self, file_name, encoding="utf-8"):
        # check file is obj file
        if not file_name.endswith(".obj"):
            raise ValueError("model file should be an obj file")
        self.file_name = file_name
        self.encoding = encoding
        self.vertices = []
        self.texture_coords = []
        self.normals = []
        self.faces = []

    def parse(self):
        lines = self.__line_generator(self.file_name, self.encoding)
        for line in lines:
            split = line.split()
            if len(split) < 2:
                # empty line or no content
                continue
            prefix = split[0]
            # parse all vertex, texture, normal and face lines, ignore the rest
            if prefix == 'v':
                self.__parse_v(line)
            elif prefix == 'vt':
                self.__parse_vt(line)
            elif prefix == 'vn':
                self.__parse_vn(line)
            elif prefix == 'f':
                self.__parse_f(line)
        return Scene(self.vertices, self.texture_coords, self.normals, self.faces)

    @staticmethod
    def __line_generator(file_name, encoding):
        file = open(file_name, mode='r', encoding=encoding)
        for line in file:
            yield line
        file.close()

    def __parse_v(self, line):
        """parse vertex and add to list"""
        parts = line.split()
        if len(parts) is not 4:
            raise ValueError("Vertex should have three dimensions")
        vertex = Vertex(float(parts[1]), float(parts[2]), float(parts[3]))
        self.vertices.append(vertex)

    def __parse_vt(self, line):
        """parse texture and add to list"""
        parts = line.split()
        if len(parts) is not 3:
            raise ValueError("Texture coordinate should have two dimensions")
        vt = [float(parts[1]), float(parts[2])]
        self.texture_coords.append(vt)

    def __parse_vn(self, line):
        """parse normal and add to list"""
        parts = line.split()
        if len(parts) is not 4:
            raise ValueError("Normals should have three dimensions")
        vn = [float(parts[1]), float(parts[2]), float(parts[3])]
        self.normals.append(vn)

    def __parse_f(self, line):
        """
        parse face and add to list
        face are saved as triangles
        """
        # store the first, previous and current vertex for triangulation
        first, prev, current = None, None, None
        for i, vertex in enumerate(line.split()[1:]):
            # iterate all vertices of a line
            parts = vertex.split('/')
            if len(parts) is not 3 or parts[1] is '':
                # only "f v/vt/vn" is accepted
                raise ValueError("Vertices of faces should have texture coords and normals")

            # obj is starts at idx 1, but python list at idx 0 --> decrease index
            v_idx = int(parts[0]) - 1
            vt_idx = int(parts[1]) - 1
            vn_idx = int(parts[2]) - 1
            prev = current
            current = (v_idx, vt_idx, vn_idx)
            if i == 0:
                first = current
            if i >= 2:
                # triangulate and create face
                first_vertex = self.vertices[first[0]]
                prev_vertex = self.vertices[prev[0]]
                current_vertex = self.vertices[current[0]]
                #           vertex1,      vertex2,     vertex3,        vt1_idx,  vt2_idx, vt3_idx,    vn_idx
                face = Face(first_vertex, prev_vertex, current_vertex, first[1], prev[1], current[1], first[2])

                # add this face to every adjacent vertex
                first_vertex.add_face(face)
                prev_vertex.add_face(face)
                current_vertex.add_face(face)
                # add to faces list
                self.faces.append(face)
