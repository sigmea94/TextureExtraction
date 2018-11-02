from extendedobjparser.vertex import Vertex


class FaceParser(object):

    def __init__(self, file_name, encoding="utf-8"):
        self.file_name = file_name
        self.encoding = encoding

        self.faces = None   # faces for current mesh
        self.meshes = []    # list of faces per mesh

    def parse(self):
        lines = line_generator(self.file_name, self.encoding)
        for line in lines:
            split = line.split()
            if len(split) < 2:
                # empty line or no content
                continue
            prefix = split[0]
            if prefix == 'o':
                # 'o' indicates a new named objects
                # start new faces list for new mesh
                self.faces = []
                self.meshes.append(self.faces)
            elif prefix == 'f':
                # 'f' indicates a face
                if self.faces is None:
                    # start new faces for unnamed object
                    self.faces = []
                    self.meshes.append(self.faces)
                face = parse_face(line)
                self.faces.append(face)
        return self.meshes


# generate vertex and add to faces
def parse_face(line):
    face = []   # list of vertices: face consists of multiple vertices
    for i, vertex in enumerate(line.split()[1:]):   # each vertex is separated by a space
        has_texture = False
        has_normal = False
        parts = vertex.split('/')   # each element of a vertex is separated by a slash
        if len(parts) == 2:         # two parts: v/vt
            has_texture = True
        elif len(parts) == 3:       # three parts: v//vn or v/vt/vn
            if parts[1] != '':
                has_texture = True
            has_normal = True

        v_idx = int(parts[0]) - 1
        vt_idx = int(parts[1]) - 1 if has_texture else None
        vn_idx = int(parts[2]) - 1 if has_normal else None
        vertex = Vertex(v_idx, vt_idx, vn_idx)
        face.append(vertex)
    return face


def line_generator(file_name, encoding):
    file = open(file_name, mode='r', encoding=encoding)
    for line in file:
        yield line
    file.close()
