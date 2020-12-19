import bpy
import bmesh
from mathutils import Vector, Matrix

from .. ops import create_point_cloud, new_object
from .. utils.utils import matrix_make_positive


def create_grid(*inputstreams, options={}):
    ops_type = options['ops_type']
    matrix = options['matrix']
    size = options['size']
    x_segments = options['x_segments']
    y_segments = options['y_segments']

    obj = new_object(name='OUT_LIVE_' + ops_type)
    me = obj.data
    # Get a BMesh representation
    bm = bmesh.new()

    bmesh.ops.create_grid(bm, x_segments=x_segments, y_segments=y_segments, size=size, matrix=Matrix(), calc_uvs=True)

    if matrix.is_negative:
        matrix = matrix_make_positive(matrix)

    # Finish up, write the bmesh back to the mesh
    bm.to_mesh(me)
    me.update()
    bm.free()

    obj.matrix_world = matrix
    return ([obj], None)


def create_point(*inputstreams, options={}):
    ops_type = options['ops_type']
    matrix = options['matrix']
    location = options['location']

    name = 'OUT_LIVE_' + ops_type
    obj, _ = create_point_cloud(name, options={'coords': [location], 'edges': [], 'faces': []})

    if matrix.is_negative:
        matrix = matrix_make_positive(matrix)

    obj.matrix_world = matrix
    return ([obj], None)


def create_uvsphere(*inputstreams, options={}):
    ops_type = options['ops_type']
    matrix = options['matrix']
    diameter = options['diameter']
    segments = options['segments']

    obj = new_object(name='OUT_LIVE_' + ops_type)
    me = obj.data
    # Get a BMesh representation
    bm = bmesh.new()
    #bm.from_mesh(me)

    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=segments, diameter=diameter, matrix=matrix, calc_uvs=True)

    if matrix.is_negative:
        matrix = matrix_make_positive(matrix)

    # Finish up, write the bmesh back to the mesh
    bm.to_mesh(me)
    me.update()
    bm.free()

    obj.matrix_world = matrix
    return ([obj], None)


def create_icosphere(*inputstreams, options={}):
    ops_type = options['ops_type']
    matrix = options['matrix']
    diameter = options['diameter']
    subdivisions = options['subdivisions']

    obj = new_object(name='OUT_LIVE_' + ops_type)
    me = obj.data
    # Get a BMesh representation
    bm = bmesh.new()
    #bm.from_mesh(me)

    bmesh.ops.create_icosphere(bm, subdivisions=subdivisions, diameter=diameter, matrix=Matrix(), calc_uvs=True)

    if matrix.is_negative:
        matrix = matrix_make_positive(matrix)

    # Finish up, write the bmesh back to the mesh
    bm.to_mesh(me)
    me.update()
    bm.free()

    obj.matrix_world = matrix
    return ([obj], None)


def create_cone(*inputstreams, options={}):
    ops_type = options['ops_type']
    matrix = options['matrix']
    cap_ends = options['cap_ends']
    cap_tris = options['cap_tris']
    segments = options['segments']
    diameter1 = options['diameter1']
    diameter2 = options['diameter2']
    depth = options['depth']

    obj = new_object(name='OUT_LIVE_' + ops_type)
    me = obj.data
    # Get a BMesh representation
    bm = bmesh.new()
    #bm.from_mesh(me)

    bmesh.ops.create_cone(bm, cap_ends=cap_ends, cap_tris=cap_tris, segments=segments, diameter1=diameter1, diameter2=diameter2, depth=depth, matrix=Matrix(), calc_uvs=True)

    if matrix.is_negative:
        matrix = matrix_make_positive(matrix)

    # Finish up, write the bmesh back to the mesh
    bm.to_mesh(me)
    me.update()
    bm.free()

    obj.matrix_world = matrix
    return ([obj], None)


def create_cylinder(*inputstreams, options={}):
    ops_type = options['ops_type']
    matrix = options['matrix']
    cap_ends = options['cap_ends']
    cap_tris = options['cap_tris']
    segments = options['segments']
    diameter = options['diameter']
    depth = options['depth']

    obj = new_object(name='OUT_LIVE_' + ops_type)
    me = obj.data
    # Get a BMesh representation
    bm = bmesh.new()
    #bm.from_mesh(me)

    bmesh.ops.create_cone(bm, cap_ends=cap_ends, cap_tris=cap_tris, segments=segments, diameter1=diameter, diameter2=diameter, depth=depth, matrix=Matrix(), calc_uvs=True)

    if matrix.is_negative:
        matrix = matrix_make_positive(matrix)

    # Finish up, write the bmesh back to the mesh
    bm.to_mesh(me)
    me.update()
    bm.free()

    obj.matrix_world = matrix
    return ([obj], None)


def create_circle(*inputstreams, options={}):
    ops_type = options['ops_type']
    matrix = options['matrix']
    cap_ends = options['cap_ends']
    cap_tris = options['cap_tris']
    radius = options['radius']
    segments = options['segments']

    obj = new_object(name='OUT_LIVE_' + ops_type)
    me = obj.data
    # Get a BMesh representation
    bm = bmesh.new()
    #bm.from_mesh(me)

    bmesh.ops.create_circle(bm, cap_ends=cap_ends, cap_tris=cap_tris, segments=segments, radius=radius, matrix=Matrix(), calc_uvs=True)

    if matrix.is_negative:
        matrix = matrix_make_positive(matrix)

    # Finish up, write the bmesh back to the mesh
    bm.to_mesh(me)
    me.update()
    bm.free()

    obj.matrix_world = matrix
    return ([obj], None)


def create_cube(*inputstreams, options={}):
    ops_type = options['ops_type']
    matrix = options['matrix']
    size = options['size']

    obj = new_object(name='OUT_LIVE_' + ops_type)
    me = obj.data
    # Get a BMesh representation
    bm = bmesh.new()
    #bm.from_mesh(me)

    # (loc, rot, sca) = matrix.decompose()
    # sca = [e if abs(e) > 0.0001 else 0.0001 for e in sca]
    # sca = Vector(sca)
    # matrix = Matrix.Translation(loc) @ rot.to_matrix().to_4x4() @ Matrix.Diagonal(sca).to_4x4()

    bmesh.ops.create_cube(bm, size=size, matrix=Matrix(), calc_uvs=True)

    # if sca.x * sca.y * sca.z < 0: # flipping on 1 or 3 axis, is to also flip the normals
    if matrix.is_negative:
        matrix = matrix_make_positive(matrix)
        # bmesh.ops.reverse_faces(bm, faces=bm.faces, flip_multires=False)
        # for face in bm.faces:
        #     face.normal_flip()

    # Finish up, write the bmesh back to the mesh
    bm.to_mesh(me)
    me.update()
    bm.free()

    obj.matrix_world = matrix
    return ([obj], None)


def create_mesh_from_selection(inputstream0, options={}):
    if len(inputstream0) == 0:
        return ([], None)

    ops_type = options['ops_type']
    matrix = options['matrix']
    faces = options['faces']
    height = options['distance']

    if height == 0.0:
        height = 0.0001

    obj = new_object(name='OUT_LIVE_' + ops_type)
    me = obj.data
    # Get a BMesh representation
    bm = bmesh.new()
    #bm.from_mesh(me)

    from_obj = inputstream0[0]
    f_indices = [int(f) for f in faces.split()]

    if len(f_indices) < 1:
        return ([], None)

    for face_index in f_indices:
        face = from_obj.data.polygons[face_index]
        new_verts = [bm.verts.new(from_obj.data.vertices[vert].co) for vert in face.vertices]
        bm.faces.new(new_verts)

    geom = bmesh.ops.extrude_face_region(bm, geom = bm.faces)['geom']
    verts = [elem for elem in geom if isinstance(elem, bmesh.types.BMVert)]

    bm.faces.ensure_lookup_table()

    (loc, rot, sca) = matrix.decompose()
    bmesh.ops.translate(bm, vec = bm.faces[0].normal * height, verts = verts )

    if height > 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces, flip_multires=False)
        # for face in bm.faces:
        #     face.normal_flip()

    # Finish up, write the bmesh back to the mesh
    bm.to_mesh(me)
    me.update()
    bm.free()

    return ([obj], None)
