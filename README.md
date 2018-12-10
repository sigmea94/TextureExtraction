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
    * up direction ("up_direction"")
* image file from which the texture is to be extracted

The aspect ratio of the camera is assumed to be equal to that of the image. The vertical fov is calculated from the
horizontal fov and the aspect ratio. Furthermore a base texture can be provided, which is then refined. Image files are
read with the [pillow python module](https://python-pillow.org/).

In order to determine the texture for each face, unnecessary faces are removed. As a result the application is more
efficient (less vertices to project) and more important a texture is only applied for visible faces. To find out the
corresponding pixels for a face, the scene is projected onto the image via the "viewing pipeline".

In total following steps are performed: 
* __back-face culling:__ remove faces that point away from the viewpoint. In addition, faces which are not back facing
but are barely facing the camera (angles of about 85 degree or more) are culled too. From such steep faces, it does not
make sense to extract the texture, as this leads to a poor result.
* __view transformation:__ translate and rotate the scene into the camera coordinate system, which is specified by the
camera position, the look direction and the up direction
* __perspective transformation:__ transforms the view frustum into a cuboid. In this application a special perspective
transformation is used in which the z-values of the vertices remain unchanged. This makes it easier to remove hidden
surfaces
* __frustum culling:__ remove faces outside the field of view of the camera. This can easily be done because the view
volume is a simple cuboid
* __occlusion culling:__ remove faces which are hidden behind other faces. To achieve this, a depth buffer is used which
stores the smallest z value for each pixel of the buffer. In a second step, all vertices are compared to the corresponding
value of the buffer and are discarded if the buffer contains a smaller value. It is possible to determine a small threshold
to compensate for the inaccuracy of float numbers and self occlusion due to the discrete buffer resolution. With a higher
threshold, the resolution can be reduced, which increases performance. The best threshold depends on the model (distances
between occluded faces)
* __screen transformation:__ transforms each vertex on a pixel of the screen (in this application a pixel of the image).
Therefore the z value will be set to zero.
* __pixel copy:__ for every pixel on the texture copy the corresponding pixel from the image


The pixel-copy algorithm is crucial to the performance of the application and the quality of the generated texture. There
are several possible implementations:
* Scanline: Use a scanline algorithm to iterate only the pixels within the triangle.
    * Best performance and good quality
* Bounding Box: Calculate a Bounding box of the triangle on the texture. Iterate all pixels within the bounding box. For
each pixel within the triangle calculate the corresponding image pixel via barycentric coordinates.
    * Good performance and good quality
* Flat Triangle: Similar to Bounding Box algorithm, however, only the pixel of the triangles are iterated. To achieve
this the triangle must first be divided into a bottom and top flat triangle.
    * Similar performance and quality, but more complex algorithm 
* Flood Fill: Start from the center of the texture triangle and iterate every pixel via flood fill.
    * Bad performance, same quality as bounding box algorithm.
* direct Barycentric Interpolation: Calculate the optimal step size for the barycentric interpolation from the number of
pixels of the triangle sides. Iterate all barycentric coordinates for the texture and use them for the image pixel too.
    * Slightly worse performance and worst result with some missing pixels in the texture.
* Transform and Paste: Transform the triangle on the image to fit the triangle on the texture (size and rotation). Copy
and paste the whole triangle at once.
    * Bad performance but best quality.

Ranking in terms of performance:  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Scanline > Bounding Box > Flat Triangle > Barycentric > Transform and Paste > Flood Fill

Ranking in terms of quality:  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Transform and Paste > Scanline = Bounding Box = Flat Triangle = Flood Fill > Barycentric

Notes:
* For algorithms that don't use barycentric coordinates directly, they can be calculated using the ratio of total area to
sub-triangle area.
* Performance specifications refer to the sequential execution of the algorithm. For the final application a parallel
execution should be used.
* Performance depends on texture resolution and model size too.
* Quality ratings are subjective without using numerical measures
* These algorithms can be used in a modified version for the depth buffer calculation too.
         
#### Example Extraction
see Wiki