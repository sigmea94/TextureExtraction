def save(obj, file_path):
    # writes obj to file
    # works only for fully unwrapped meshes with normals
    f = open(file_path, 'w')
    for v in obj.vertices:
        f.write("v " + str(v[0]) + " " + str(v[1]) + " " + str(v[2]) + "\n")

    for vt in obj.parser.tex_coords:
        f.write("vt " + str(vt[0]) + " " + str(vt[1]) + "\n")

    for vn in obj.parser.normals:
        f.write("vn " + str(vn[0]) + " " + str(vn[1]) + " " + str(vn[2]) + "\n")

    for name, mesh in obj.meshes.items():
        f.write("o " + name + "\n")
        for face in mesh.faces:
            face_line = "f "
            for v in face:
                face_line += str(v.v_idx + 1) + "/" + str(v.vt_idx + 1) + "/" + str(v.vn_idx + 1) + " "
            f.write(face_line + "\n")

    f.close()
