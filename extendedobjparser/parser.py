import pywavefront
from extendedobjparser.faceparser import FaceParser


class Parser:

    def __init__(
            self,
            file_name,
            strict=False,
            encoding="utf-8",
            create_materials=True,
    ):
        self.file_name = file_name
        self.strict = strict
        self.encoding = encoding
        self.create_materials = create_materials
        # no cache support for extended parsing

    def parse(self):
        # parse obj using pywavefront module
        obj = pywavefront.Wavefront(self.file_name, self.strict, self.encoding, self.create_materials, False, True, False)
        # parse faces separately
        face_meshes = FaceParser(self.file_name, self.encoding).parse()

        # add parsed faces to corresponding meshes
        for i, mesh in enumerate(obj.mesh_list):
            mesh.faces = face_meshes[i]
            mesh.has_faces = len(face_meshes[i]) > 0
        return obj
