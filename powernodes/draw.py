import bpy
import bgl
import gpu
from math import radians
import numpy as np
from random import random, seed
from mathutils import Matrix
from mathutils import Vector
from gpu_extras.batch import batch_for_shader
from gpu_extras.presets import draw_texture_2d
from gpu_extras.presets import draw_circle_2d

import bpy.utils.previews

from . utils.utils import calc_bbox_center

WIDTH = 256
HEIGHT = 256

POINT_CLOUD_LIMIT = 10000

PREVIEW_COLLECTIONS = {}

offscreen = gpu.types.GPUOffScreen(WIDTH, HEIGHT)

def draw():
    context = bpy.context
    scene = context.scene

    view_matrix = scene.camera.matrix_world.inverted()

    projection_matrix = scene.camera.calc_matrix_camera(
        context.evaluated_depsgraph_get(), x=WIDTH, y=HEIGHT)

    offscreen.draw_view3d(
        scene,
        context.view_layer,
        context.space_data,
        context.region,
        view_matrix,
        projection_matrix)

    bgl.glDisable(bgl.GL_DEPTH_TEST)


vert_shader = '''
    uniform mat4 ModelViewProjectionMatrix;

    #ifdef USE_WORLD_CLIP_PLANES
        uniform mat4 ModelMatrix;
    #endif

    in vec3 pos;
    in vec4 color;
    in vec3 normal;

    out vec4 finalColor;
    flat out vec3 finalNormal;

    void main()
    {
        gl_Position = ModelViewProjectionMatrix * vec4(pos, 1.0);
        finalColor = color;
        finalNormal = normalize(normal);

    #ifdef USE_WORLD_CLIP_PLANES
        world_clip_planes_calc_clip_distance((ModelMatrix * vec4(pos, 1.0)).xyz);
    #endif
}
'''

frag_shader = '''
    in vec4 finalColor;
    flat in vec3 finalNormal;
    out vec4 fragColor;

    void main()
    {
        vec3 normal = normalize(finalNormal);
        vec3 light = normalize(vec3(-1.0, -10.0, 5.0));
        float shading = dot(normal, light) * 0.1;
        fragColor = vec4(finalColor.rgb + shading, 1.0);
        fragColor = blender_srgb_to_framebuffer_space(fragColor);
    }
'''


def draw_mesh_wire(mesh):
    vertices = np.empty((len(mesh.vertices), 3), 'f')
    indices = np.empty((len(mesh.edges), 2), 'i')

    mesh.vertices.foreach_get(
        "co", np.reshape(vertices, len(mesh.vertices) * 3))
    mesh.edges.foreach_get(
        "vertices", np.reshape(indices, len(mesh.edges) * 2))

    shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'LINES', {"pos": vertices}, indices=indices)

    return (shader, batch)


def draw_mesh_pointcloud(mesh, color, preview_data):
    verts = []
    vertex_colors = []
    if preview_data:
        verts = preview_data[0]
        vertex_colors = preview_data[1]
    else:
        vertices = np.empty((len(mesh.vertices), 3), 'f')
        normals = np.empty((len(mesh.vertices), 3), 'f')

        mesh.vertices.foreach_get(
            "co", np.reshape(vertices, len(mesh.vertices) * 3))

        mesh.vertices.foreach_get(
            "normal", np.reshape(normals, len(mesh.vertices) * 3))

        step = int(len(mesh.vertices) / POINT_CLOUD_LIMIT) + 1

        verts = vertices[::step]

        colors = verts # normals[::step]#[indices]

        colors_dot = colors.dot((-1,-10,5))

        vertex_colors = np.tile(np.array(color, dtype='f'), (len(verts), 1))
        vertex_colors *= colors_dot[:,np.newaxis] * 0.1
        vertex_colors[:,3] = 1.0

    shader = gpu.shader.from_builtin('3D_SMOOTH_COLOR')
    batch = batch_for_shader(
        shader, 'POINTS',
        {"pos": verts,   "color": vertex_colors },
        #indices=indices,
    )

    return (shader, batch)


def draw_mesh_shaded(mesh, color):
    if len(mesh.polygons) > 0: # avoid crash here in calc_loop_triangles
        mesh.calc_loop_triangles()
        mesh.calc_normals_split()

    vertices = np.empty((len(mesh.vertices), 3), 'f')
    normals = np.empty((len(mesh.loop_triangles) * 3, 3), 'f')
    indices = np.empty((len(mesh.loop_triangles) * 3), 'i')

    mesh.vertices.foreach_get(
        "co", np.reshape(vertices, len(mesh.vertices) * 3))

    mesh.loop_triangles.foreach_get(
        "split_normals", np.reshape(normals, len(mesh.loop_triangles) * 9))

    mesh.loop_triangles.foreach_get(
        "vertices", np.reshape(indices, len(mesh.loop_triangles) * 3))

    verts = vertices[indices]

    #vertex_colors = [color] * len(mesh.loop_triangles) * 3
    vertex_colors = np.tile(np.array(color, dtype='f'), (len(mesh.loop_triangles) * 3, 1))


    #shader = gpu.shader.from_builtin('3D_SMOOTH_COLOR')
    #code = gpu.shader.code_from_builtin('3D_UNIFORM_COLOR')
    # shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
    shader = gpu.types.GPUShader(vert_shader, frag_shader)
    batch = batch_for_shader(
        shader, 'TRIS',
        {"pos": verts, "normal": normals,  "color": vertex_colors },
        #indices=indices,
    )

    return (shader, batch)


def copy_offscreen_to_image(obj_preview_name='OFFSCREEN_IMG', obj=None, preview_data=None):
    if not obj or not obj.data:
        return

    context = bpy.context
    edg = context.evaluated_depsgraph_get()
    mesh = obj.data

    color = obj.color
    diag_len = (obj.dimensions @ obj.matrix_world.inverted_safe()).length / 1.75 # use untransformed dimensions

    local_bbox_center = calc_bbox_center(obj)
    global_bbox_center = obj.matrix_world @ local_bbox_center

    view_matrix =  Matrix.Translation( local_bbox_center + Vector((1,-1,1)) * diag_len )
    view_matrix = view_matrix @ Matrix.Rotation(radians(45.0), 4, 'Z') @ Matrix.Rotation(radians(52.0), 4, 'X')
    view_matrix = view_matrix.inverted()

    projection_matrix = obj.calc_matrix_camera(edg)

    with offscreen.bind():
        bgl.glViewport( 0, 0, WIDTH, HEIGHT )
        bgl.glEnable(bgl.GL_DEPTH_TEST)
        bgl.glClearColor(0.0, 0.0, 0.0, 0.0)
        bgl.glClearDepth(1.0)
        bgl.glDepthMask(bgl.GL_TRUE) # explicit mask clear
        bgl.glClear(bgl.GL_COLOR_BUFFER_BIT | bgl.GL_DEPTH_BUFFER_BIT)
        bgl.glDepthFunc(bgl.GL_LESS)
        # bgl.glDepthRange(0.0, 0.9)

        # bgl.glEnable(bgl.GL_POLYGON_OFFSET_FILL)
        # bgl.glPolygonOffset(1.0, 1.0)

        bgl.glLineWidth(3.0)
        bgl.glEnable(bgl.GL_LINE_SMOOTH)
        #bgl.glEnable(bgl.GL_POLYGON_SMOOTH)

        bgl.glEnable(bgl.GL_BLEND)
        bgl.glBlendFunc(bgl.GL_SRC_ALPHA, bgl.GL_ONE_MINUS_SRC_ALPHA)

        bgl.glPointSize(5)

        with gpu.matrix.push_pop():
            # reset matrices -> use normalized device coordinates [-1, 1]
            #gpu.matrix.load_matrix(Matrix.Identity(4))
            #gpu.matrix.load_projection_matrix(Matrix.Identity(4))
            gpu.matrix.load_matrix(view_matrix)
            gpu.matrix.load_projection_matrix(projection_matrix)

            if len(mesh.vertices) < POINT_CLOUD_LIMIT and len(mesh.edges) > 0:
                (shader, batch) = draw_mesh_shaded(mesh, color)
                batch.draw(shader)

                (shader, batch) = draw_mesh_wire(mesh)
                shader.uniform_float("color", (1, 1, 1, 1))
                batch.draw(shader)
            else:
                (shader, batch) = draw_mesh_pointcloud(mesh, color, preview_data)
                batch.draw(shader)


        # using GL_FLOAT directly instead of GL_BYTE gives better perf for some reason
        buffer = bgl.Buffer(bgl.GL_FLOAT, WIDTH * HEIGHT * 4)
        # buffer = bgl.Buffer(bgl.GL_BYTE, WIDTH * HEIGHT * 4)
        # bgl.glReadBuffer(bgl.GL_COLOR_ATTACHMENT0)
        bgl.glReadBuffer(bgl.GL_BACK)
        bgl.glReadPixels(0, 0, WIDTH, HEIGHT, bgl.GL_RGBA, bgl.GL_FLOAT, buffer)
        # bgl.glReadPixels(0, 0, WIDTH, HEIGHT, bgl.GL_RGBA, bgl.GL_UNSIGNED_BYTE, buffer)

        # restore opengl defaults
        bgl.glDisable(bgl.GL_DEPTH_TEST)
        bgl.glLineWidth(1)
        bgl.glDisable(bgl.GL_BLEND)
        # bgl.glColor4f(0.0, 0.0, 0.0, 1.0) 

    #offscreen.free()

    if not 'POWER_THUMBNAILS' in PREVIEW_COLLECTIONS:
        preview_collection = bpy.utils.previews.new()
        # preview_collection.my_previews_dir = ""
        # preview_collection.my_previews = ()
        PREVIEW_COLLECTIONS['POWER_THUMBNAILS'] = preview_collection
    power_icons = PREVIEW_COLLECTIONS["POWER_THUMBNAILS"]

    # power_icons.load(file, fullpath, 'IMAGE')
    if not obj_preview_name in power_icons:
        power_icons.new(obj_preview_name)
    iprev = power_icons[obj_preview_name]
    iprev.image_size = (WIDTH,HEIGHT) # image.preview.image_size

    #iprev.image_pixels = buffer
    #iprev.image_pixels_float = off_px
    iprev.image_pixels_float.foreach_set(buffer)

    return obj_preview_name
