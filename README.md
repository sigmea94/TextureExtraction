# TextureExtractorCode

Code base for extraction of realistic textures for user avatars from RGB streams.

The target of the VIRTOOAIR framework is the reconstruction of users' avatars for VR applications based on RGB and
tracking input data.

We take the silhouette of the user in the RGB stream as a given and can therefore easily extract the relevant pixel data
for the user. Furthermore, there exists a corresponding 3D model of the user's avatar in the correct pose. The
environment is homogeneously well-lit.

The goal for the thesis is to create a UV-mappable texture for the 3D avatar from the 2D pixel-based color information.

The project is divided into two modules:
* __textureextractor:__ core-module
* __objparser:__ util-module

## Obj Parser
This module parses a wavefront obj-file into a data structure called "scene". Every vertex (v), normal (vn),
texture coordinate (vt) and face (f) is parsed. All other details which may be provided by the wavefront format are
ignored. This means especially that the grouping of faces to a specific object are lost (o value). Therefore the whole
scene acts as one single objects which may consists of several separate meshes.

A "scene" object is build as follows:
* list of 2D texture coordinates where the values indicate the pixel position as the ratio of the whole width or height
* list of normals as 3D vectors
* list of vertices with
    * 3D position (parameter pos)
    * list of adjacent faces (parameter faces)
* list of faces with
    * list of vertices of the face (parameter vertices)
    * list of texture indices for each vertex (parameter vt_indices)
    * normal index (parameter vn_idx)
    
Faces are stored as triangles. Every input mesh which is build of faces with more than three vertices is "triangulated"
into a triangle mesh. The procedure for face f with vertices v<sub>1</sub> to v<sub>n</sub> is as follows:
* iterate all vertices
* store v<sub>1</sub> v<sub>prev</sub>v<sub>current</sub>
* as soon as the iteration reaches the third vertex, a new face is created in each subsequent iteration
* the triangle pattern in each iteration is: v<sub>1</sub> v<sub>prev</sub>v<sub>current</sub>

This module is specially designed for the requirements of the core module. Therefore every face stores a direct reference
to every vertex from which it is build. Besides each vertex stores a direct reference of every adjacent face. This
structure is crucial for face culling in the core module. Moreover only unwrapped meshes can be parsed, as texture
extraction only makes sense with meshes associated with texture coordinates.

Note that the scene object provides the "save_to_file" method which creates an obj file. This is very useful for
visualising changes that have been applied to the mesh.

## Texture Extractor
This is the core module for texture extraction. For a given 3D-model, this module extracts a UV-texture map from an image
of the object.

Following input needs to be provided:
* obj file of the 3D Model (the module described in the previous section is used to parse the file)
* json file with camera parameters
    * horizontal field of view ("fov_horizontal")
    * position in the coordinate system of the model ("position")
    * look direction ("look_direction")
* image file from which the texture is to be extracted

The aspect ratio of the camera is assumed to be equal to that of the image. The vertical fov is calculated from the
horizontal fov and the aspect ratio. Furthermore a base texture can be provided, which is then refined. Image files are
read with the [pillow python module](https://python-pillow.org/).

In order to determine the texture for each face, unnecessary faces are removed. As a result the application is more
efficient (less vertices to project) and more important a texture is only applied for visible faces. To find out the
corresponding pixels for a face, the scene is projected onto the image via the "viewing pipeline".

In total following steps are performed: 
* __back-face culling:__ remove faces that point away from the viewpoint
* __view transformation:__ translate and rotate the scene into the camera coordinate system
* __frustum culling:__ remove faces outside the field of view of the camera. Note that frustum culling after the
perspective projection would be simpler. However, it is done before to determine the best near and far plane for the 
perspective projection.
* ...

#### Example Extraction
see Wiki