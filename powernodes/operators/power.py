import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from math import radians, sqrt

from .. ops import *
from .. parse import attribute_create, attribute_get, evaluate_expression, extract_custom_attribute_layers, evaluate_expression_foreach, TYPE_INITIAL_VALUE
from .. utils.utils import collinear, calc_bbox_center, matrix_make_positive, curve_length, timer_start, timer_end

import numpy as np

from . bool.csg.numba.core import bool_csg_mesh
import numba as nb
from numba import jit, cuda


def transform_operator(inputstream, options={}):
    apply_transform = options['apply_transform']
    use_local_space = options['use_local_space']
    use_relative = options['use_relative']
    use_radians = options['use_radians']
    location = options['loc']
    rotation = options['rot']
    scale = options['sca']

    if not use_radians:
        rotation = [radians(rot) for rot in rotation]

    for obj in inputstream:
        if use_local_space:
            rot_inv = obj.rotation_euler.to_matrix().inverted()
            location = location @ rot_inv

        if use_relative == True:
            # transfrom in local space
            obj.location += location

            if use_local_space:
                obj.rotation_euler.rotate_axis("X", rotation[0])
                obj.rotation_euler.rotate_axis("Y", rotation[1])
                obj.rotation_euler.rotate_axis("Z", rotation[2])
            else:
                obj.rotation_euler.x += rotation[0]
                obj.rotation_euler.y += rotation[1]
                obj.rotation_euler.z += rotation[2]

            obj.scale *= scale

        else:
            # transfrom in global space
            obj.location = location

            if use_local_space:
                obj.rotation_euler.rotate_axis("X", -obj.rotation_euler.x + rotation[0])
                obj.rotation_euler.rotate_axis("Y", -obj.rotation_euler.y + rotation[1])
                obj.rotation_euler.rotate_axis("Z", -obj.rotation_euler.z + rotation[2])
            else:
                obj.rotation_euler.x = rotation[0]
                obj.rotation_euler.y = rotation[1]
                obj.rotation_euler.z = rotation[2]

            obj.scale = scale

        if apply_transform:
            transform_apply_object([obj])

    # obj.update_tag()

    return (inputstream, None)


def bool_csg(a, b, operation_type):
    polygons = None
    if operation_type == 'DIFFERENCE':
        polygons = a.subtract(b).toPolygons()
    elif operation_type == 'UNION':
        polygons = a.union(b).toPolygons()
    elif operation_type == 'INTERSECT':
        polygons = a.intersect(b).toPolygons()
    return polygons


def bool_csg_numba(target_obj, cutter_obj, operation_type):
    # start CSG
    target_obj.data.calc_loop_triangles()
    cutter_obj.data.calc_loop_triangles()

    # connect_concave_bmesh_operator(target_obj)
    # connect_concave_bmesh_operator(cutter_obj)
    mesh = target_obj.data
    mesh2 = cutter_obj.data

    timer_start()
    a_polygons = [{'vertices':[mesh.vertices[vert_idx].co[:] for vert_idx in loop_triangle.vertices], 'shared': loop_triangle.polygon_index} for loop_triangle in mesh.loop_triangles]
    # a_polygons = [{'vertices':[mesh.vertices[mesh.loops[loop_idx].vertex_index].co[:] for loop_idx in p.loop_indices], 'shared': p.index, 'selected': (1 if p.select else 0)} for p in mesh.polygons]
    timer_end('target load ')

    timer_start()
    total_target_count = len(target_obj.data.polygons)
    b_polygons = [{'vertices':[mesh2.vertices[vert_idx].co[:] for vert_idx in loop_triangle.vertices], 'shared': loop_triangle.polygon_index + total_target_count} for loop_triangle in mesh2.loop_triangles]
    # b_polygons = [{'vertices':[mesh2.vertices[mesh2.loops[loop_idx].vertex_index].co[:] for loop_idx in p.loop_indices], 'shared': p.index + total_target_count, 'selected': (1 if p.select else 0)} for p in mesh2.polygons]
    timer_end('cutter load ')

    timer_start()
    polygons = bool_csg_mesh(a_polygons, b_polygons, operation_type)
    timer_end('bool op ')

    timer_start()

    vertices = []
    vnormals = []
    faces = []
    normals = []
    colors = []
    count = 0
    for polygon in polygons:
        indices = []
        shared = 0
        for v in polygon:
            pos = (v[0], v[1], v[2])
            shared = int(v[3])
            # if pos not in vertices:
            vertices.append(pos)
            index = count
            indices.append(index)
            count += 1
        faces.append(indices)
        # colors.append(shared)

    timer_end('to poly ')

    timer_start()

    csg_mesh = bpy.data.meshes.new("bool_new_mesh")
    csg_mesh.from_pydata(vertices, [], faces)
    for index, face in enumerate(csg_mesh.polygons): setattr(face, 'material_index', int(polygons[index][0][3]))
    csg_mesh.update()

    old_mesh = target_obj.data
    target_obj.data = csg_mesh
    target_obj.data.update()

    # remove the old mesh from the .blend
    if old_mesh:
        bpy.data.meshes.remove(old_mesh)

    timer_end('to bmesh ')

    timer_start()

    # run clean up multiple times
    # weld_operator([target_obj], {'distance': 0.00001})
    fix_t_junction(target_obj, {'distance': 0.00001})
    fix_t_junction(target_obj, {'distance': 0.00001})
    # weld_operator([target_obj], {'distance': 0.00001})
    limited_dissolve_bmesh_operator(target_obj)
    dissolve_tess_edges(target_obj)
    limited_dissolve_bmesh_operator(target_obj)
    dissolve_tess_edges(target_obj)
    limited_dissolve_bmesh_operator(target_obj)

    timer_end('clean up ')

    return

    # # end CSG


def boolean_operator(inputstream0, inputstream1, options={}):
    solver = options['solver']
    operation_type = options['operation_type']
    error_tolerance = options['error_tolerance']
    fix_boolean = options['fix_boolean']

    for target_obj in inputstream0:
        for cutter_obj in inputstream1:
            opts = {'tolerance': 0.0001, 'angle': 0.0001, 'shift': 0.0001}

            if len(target_obj.data.polygons) == 0 or len(cutter_obj.data.polygons) == 0:
                continue

            if operation_type == 'SLICE':
                operation_type = 'DIFFERENCE'
                solidify_operator([cutter_obj], options={
                    'solidify_mode': 'EXTRUDE',
                    'thickness': 0.00001,
                    'offset': -1,
                    'use_rim': True,
                    'use_rim_only': False})

            if fix_boolean:
                # fix coplanar
                transform_apply_object([cutter_obj])
                sca = Matrix.Diagonal((1.00001, 1.00001, 1.00001)).to_4x4()
                cutter_obj.data.transform(sca)

            if solver == 'CSG':
                transform_apply_object([target_obj, cutter_obj])
                bool_csg_numba(target_obj, cutter_obj, operation_type)
            else:
                mod = target_obj.modifiers.new(name=operation_type + '_' + cutter_obj.name, type='BOOLEAN')
                mod.solver = solver
                mod.operation = operation_type
                mod.object = cutter_obj
                mod.double_threshold = error_tolerance

                #bpy.ops.object.modifier_apply({"object": target_obj}, apply_as='DATA', modifier=bool_mod.name)

                # get a reference to the current obj.data
                old_mesh = target_obj.data

                (ctx, edp) = capture_context([target_obj, cutter_obj])
                object_eval = target_obj.evaluated_get(edp)
                new_mesh_from_eval = bpy.data.meshes.new_from_object(object_eval, preserve_all_data_layers=True, depsgraph=edp)

                # object will still have modifiers, remove them
                target_obj.modifiers.clear()

                # assign the new mesh to obj.data 
                target_obj.data = new_mesh_from_eval

                # remove the old mesh from the .blend
                if old_mesh:
                    bpy.data.meshes.remove(old_mesh)

    return (inputstream0, None)


@cuda.jit
def numba_push_cuda(a, val):
    arr_len = a.shape[0]
    i = cuda.grid(1)
    if i < arr_len:
        base = i // 3 * 3
        dist = (a[base] ** 2 + a[base+1] ** 2 + a[base+2] ** 2) ** 0.5 
        mean = 0.0
        if dist > 0:
            mean = a[i] / dist
        a[i] = a[i] + mean * val


def explode_numba(vertices, val):
    threadsperblock = 32
    blockspergrid = math.ceil(vertices.shape[0] / threadsperblock)
    numba_push_cuda[blockspergrid, threadsperblock](vertices, val)


def explode_operator(objects=[], options={}):
    if len(objects) < 1:
        return ([], None)

    value = options['value']

    obj = objects[0]
    me = obj.data

    # for vert in obj.data.vertices:
    #     if not vert.hide:
    #         vert.co += vert.normal * value


    # for vert in obj.data.vertices:
    #     if not vert.hide:
    #         direction = (vert.co - center).normalized()
    #         vert.co += direction * value

    timer_start()

    coords_cpu = np.empty((len(me.vertices) *3), dtype='f')
    #coords = np.frombuffer(np.asarray(me.vertices, 'f'))

    me.vertices.foreach_get('co', coords_cpu)

    #numba

    explode_numba(coords_cpu, value)

    timer_end('numba cuda ')

    me.vertices.foreach_set('co', coords_cpu)

    return (objects, None)

def bevel_operator(inputstream, options={}):
    mode = options['mode']
    expression = options['expression']
    offset = options['offset']
    offset_type = options['offset_type']
    segments = options['segments']
    profile = options['profile']
    clamp_overlap = options['clamp_overlap']
    vertex_only = options['vertex_only']

    for obj in inputstream:
        me = obj.data

        # Get a BMesh representation
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()

        elements = []
        if mode == 'VERT':
            elements = bm.verts
        if mode == 'EDGE':
            elements = bm.edges
        if mode == 'FACE':
            elements = bm.faces

        selected_elements = []
        try:
            values = evaluate_expression_foreach(elements, expression, obj, me, bm, mode)
            selected_elements = [elem for elem, value in zip(elements, values) if bool(value)]
        except Exception as e:
            print('Failed to evaluate expression: ', str(e))

        faces = bmesh.ops.bevel(bm,
                        geom=selected_elements,
                        offset=offset,
                        offset_type=offset_type, #'PERCENT', #OFFSET PERCENT
                        segments=segments,
                        profile=profile,
                        affect='VERTICES' if vertex_only else 'EDGES',
                        clamp_overlap=clamp_overlap,
                        material=-1)

        # Finish up, write the bmesh back to the mesh
        bm.to_mesh(me)
        me.update()
        bm.free()

    return (inputstream, None)


def extrude_operator(inputstream, options={}):
    mode = options['mode']
    offset_displace = Vector(options['offset_displace'])
    expression = options['expression']
    use_keep_orig = options['use_keep_orig']
    use_normal_flip = options['use_normal_flip']
    use_normal_from_adjacent = options['use_normal_from_adjacent']
    use_dissolve_ortho_edges = options['use_dissolve_ortho_edges']

    for obj in inputstream:
        me = obj.data

        # Get a BMesh representation
        bm = bmesh.new()
        bm.from_mesh(me)

        bm.normal_update()

        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        elements = []
        if mode == 'VERT':
            elements = bm.verts
        if mode == 'EDGE':
            elements = bm.edges
        if mode == 'FACE':
            elements = bm.faces
        if mode == 'REGION':
            elements = bm.faces

        selected_elements = []
        try:
            values = evaluate_expression_foreach(elements, expression, obj, me, bm, mode)
            selected_elements = [elem for elem, value in zip(elements, values) if bool(value)]
        except Exception as e:
            print('Failed to evaluate expression: ', str(e))

        if mode == 'VERT':
            geom = bmesh.ops.extrude_vert_indiv(bm, verts = selected_elements)['verts']

            verts = [elem for elem in geom if isinstance(elem, bmesh.types.BMVert)]

            bm.verts.ensure_lookup_table()

            normals = [vert.normal.copy() for vert in verts]
            for index, vert in enumerate(verts):
                rot_quat = normals[index].to_track_quat("Z", "X")
                rot_mat = rot_quat.to_matrix().to_4x4()
                displace_vec = rot_mat @ offset_displace
                vert.co += displace_vec                
                # bmesh.ops.translate(bm, vec = rot_mat @ offset_displace, verts = [vert])

        if mode == 'EDGE':
            geom = bmesh.ops.extrude_edge_only(bm, edges = selected_elements, use_normal_flip=use_normal_flip)['geom']

            # edges = [elem for elem in geom if isinstance(elem, bmesh.types.BMEdge)]

            # bm.edges.ensure_lookup_table()

            # normals = [(edge.verts[0].co + edge.verts[1].co) / 2 for edge in edges]
            # for index, edge in enumerate(edges):
            #     rot_quat = normals[index].to_track_quat("Z", "X")
            #     rot_mat = rot_quat.to_matrix().to_4x4()
            #     bmesh.ops.translate(bm, vec = rot_mat @ offset_displace, verts = edge.verts )

            verts = [elem for elem in geom if isinstance(elem, bmesh.types.BMVert)]

            bm.verts.ensure_lookup_table()

            normals = [vert.normal.copy() for vert in verts]
            for index, vert in enumerate(verts):
                rot_quat = normals[index].to_track_quat("Z", "X")
                rot_mat = rot_quat.to_matrix().to_4x4()
                displace_vec = rot_mat @ offset_displace
                vert.co += displace_vec
                # bmesh.ops.translate(bm, vec = rot_mat @ offset_displace, verts = [vert])

        if mode == 'FACE':
            timer_start()
            geom = bmesh.ops.extrude_discrete_faces(bm, faces = selected_elements, use_normal_flip=use_normal_flip)['faces']

            faces = [elem for elem in geom if isinstance(elem, bmesh.types.BMFace)]

            bm.faces.ensure_lookup_table()

            for face in faces:
                rot_quat = face.normal.to_track_quat("Z", "X")
                rot_mat = rot_quat.to_matrix().to_4x4()
                displace_vec = rot_mat @ offset_displace
                for vert in face.verts:
                    vert.co += displace_vec
                # bmesh.ops.translate(bm, vec = rot_mat @ offset_displace, verts = face.verts )

            timer_end('extrude face: ')

        if mode == 'REGION':
            geom = bmesh.ops.extrude_face_region(bm, geom = selected_elements,
                use_keep_orig=use_keep_orig,
                use_normal_flip=use_normal_flip,
                use_normal_from_adjacent=use_normal_from_adjacent)['geom']

            faces = [elem for elem in geom if isinstance(elem, bmesh.types.BMFace)]

            bm.faces.ensure_lookup_table()

            normals = [face.normal.copy() for face in faces]
            for index, face in enumerate(faces):
                rot_quat = normals[index].to_track_quat("Z", "X")
                rot_mat = rot_quat.to_matrix().to_4x4()
                displace_vec = rot_mat @ offset_displace
                for vert in face.verts:
                    vert.co += displace_vec
                # bmesh.ops.translate(bm, vec = rot_mat @ offset_displace, verts = face.verts )

        # Finish up, write the bmesh back to the mesh
        bm.to_mesh(me)
        me.update()
        bm.free()

    return (inputstream, None)


def inset_operator(inputstream, options={}):
    mode = options['mode']
    expression = options['expression']
    thickness = options['thickness']
    depth = options['depth']
    use_boundary = options['use_boundary']
    use_even_offset = options['use_even_offset']
    use_interpolate = options['use_interpolate']
    use_relative_offset = options['use_relative_offset']
    use_edge_rail = options['use_edge_rail']
    use_outset = options['use_outset']

    for obj in inputstream:
        me = obj.data

        # Get a BMesh representation
        bm = bmesh.new()
        bm.from_mesh(me)

        bm.normal_update()

        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        faces = []
        try:
            elements = bm.faces
            values = evaluate_expression_foreach(elements, expression, obj, me, bm, mode)
            faces = [elem for elem, value in zip(elements, values) if bool(value)]
        except Exception as e:
            print('Failed to evaluate expression: ', str(e))

        if mode == 'FACE':
            geom = bmesh.ops.inset_individual(bm,
                faces=faces,
                thickness=thickness,
                depth=depth,
                use_even_offset=use_even_offset,
                use_interpolate=use_interpolate,
                use_relative_offset=use_relative_offset)

        if mode == 'REGION':
            geom = bmesh.ops.inset_region(bm,
                faces=faces,
                faces_exclude=[],
                use_boundary=use_boundary,
                use_even_offset=use_even_offset,
                use_interpolate=use_interpolate,
                use_relative_offset=use_relative_offset,
                use_edge_rail=use_edge_rail,
                thickness=thickness,
                depth=depth,
                use_outset=use_outset)

        # Finish up, write the bmesh back to the mesh
        bm.to_mesh(me)
        me.update()
        bm.free()

    return (inputstream, None)


def weld_operator(inputstream, options={'distance': 0.00001}):
    distance = options['distance']

    for obj in inputstream:
        me = obj.data
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=distance)
        bm.to_mesh(me)
        me.update()
        bm.free()

    return (inputstream, None)


def array_operator(inputstream0, inputstream1, options={}):
    fit_type = options['fit_type']
    count = options['count']
    use_local_space = options['use_local_space']
    use_relative_offset = options['use_relative_offset']
    displace = (options['relative_offset_displace'])
    axis = options['axis']
    use_merge_vertices = options['use_merge_vertices']

    for target_obj in inputstream0:
        if len(inputstream1) > 0:
            pivot_obj = inputstream1[0]
        else:
            pivot_obj = bpy.data.objects.new('empty', None )
            pivot_obj.location = target_obj.location
            pivot_obj.rotation_euler = target_obj.rotation_euler
            # pivot_obj.parent = target_obj

        mod = target_obj.modifiers.new(name='ARRAY' + '_' + target_obj.name, type='ARRAY')
        mod.count = count
        mod.use_merge_vertices = use_merge_vertices

        if not use_local_space:
            transform_apply_object([target_obj])

        if fit_type == 'RADIAL':
            mod.use_relative_offset = False
            mod.use_object_offset = True
            # global_rot = getattr(pivot_obj.rotation_euler, axis.lower())
            # setattr(pivot_obj.rotation_euler, axis.lower(), global_rot + math.radians(360) / count)
            pivot_obj.rotation_euler.rotate_axis(axis, math.radians(360) / count) # rotate in local space
            mod.offset_object = pivot_obj

            # rot_mat = target_obj.rotation_euler.to_matrix()
            # rot_mat_inv = rot_mat.inverted()
            # target_obj.location += Vector(displace) @ rot_mat_inv
            # transform_apply_object([target_obj])

            # apply scale
            target_obj.data.transform(Matrix.Diagonal(target_obj.scale).to_4x4()) 
            target_obj.scale = Vector((1.0, 1.0, 1.0))

            # displace in local space
            target_obj.data.transform(Matrix.Translation(displace).to_4x4()) 
        else:
            mod.fit_type = fit_type
            mod.curve = pivot_obj.pn_original
            mod.use_relative_offset = use_relative_offset
            mod.relative_offset_displace = displace

        if fit_type == 'FIT_CURVE':
            curve = pivot_obj.pn_original
            curve_len = curve_length(curve)
            count = math.ceil(curve_len / target_obj.dimensions.x)
            # mod.count = count
            scale = curve_len / count
            target_obj.scale.x *=  scale / target_obj.dimensions.x
            curve_mod = target_obj.modifiers.new(name='CURVE' + '_' + target_obj.name, type='CURVE')
            curve_mod.object = curve
            curve_mod.deform_axis = 'POS_X'

        #bpy.ops.object.modifier_apply({"object": target_obj}, apply_as='DATA', modifier=bool_mod.name)

        # get a reference to the current obj.data
        old_mesh = target_obj.data

        (ctx, edp) = capture_context([target_obj, pivot_obj])
        object_eval = target_obj.evaluated_get(edp)
        new_mesh_from_eval = bpy.data.meshes.new_from_object(object_eval, preserve_all_data_layers=True, depsgraph=edp)

        # object will still have modifiers, remove them
        target_obj.modifiers.clear()

        # assign the new mesh to obj.data 
        target_obj.data = new_mesh_from_eval

        # remove the old mesh from the .blend
        if old_mesh:
            bpy.data.meshes.remove(old_mesh)

        if len(inputstream1) == 0:
            delete_object(pivot_obj)

        # # set location
        # if not is_radial:
        #     origin_set_object([target_obj])
        #     #target_obj.location -= displace * count

    return (inputstream0, None)


SWEEP_AXIS_MAP = {
    "X": {'displace': (0.0,1.0,0.0), 'scale_axis':(0.0,0.0,1.0), 'scale_axis_name': 'z'},
    "Y": {'displace': (1.0,0.0,0.0), 'scale_axis':(0.0,0.0,1.0), 'scale_axis_name': 'z'},
    "Z": {'displace': (0.0,1.0,0.0), 'scale_axis':(1.0,0.0,0.0), 'scale_axis_name': 'x'},
}

def sweep_operator(inputstream, options={}):
    count = options['count']
    displace = options['offset']
    angle = options['angle']
    deform_axis = options['axis']
    use_local_space = options['use_local_space']
    use_merge_vertices = options['use_merge_vertices']
    delete_interior = options['delete_interior']

    for target_obj in inputstream:
        # apply scale first
        target_obj.data.transform(Matrix.Diagonal(target_obj.scale).to_4x4()) 
        target_obj.scale = Vector((1.0, 1.0, 1.0))

        matrix_basis = Matrix()
        if use_local_space:
            matrix_basis = target_obj.matrix_basis.copy()
            target_obj.matrix_basis = Matrix()

        unit_scale = 1 / getattr(target_obj.dimensions, SWEEP_AXIS_MAP[deform_axis]['scale_axis_name'])
        scale_factor = 2 * math.pi / count * unit_scale
        displace_axis = SWEEP_AXIS_MAP[deform_axis]['displace']
        scale_axis = SWEEP_AXIS_MAP[deform_axis]['scale_axis']

        target_obj.location -= Vector(displace_axis) * displace
        scale_mat = Matrix.Scale(scale_factor, 4, Vector(scale_axis))
        target_obj.scale = target_obj.scale @ scale_mat
        transform_apply_object([target_obj])
        # target_obj.data.transform(Matrix.Diagonal(target_obj.scale).to_4x4()) 
        # target_obj.scale = Vector((1.0, 1.0, 1.0))

        mod = target_obj.modifiers.new(name='ARRAY' + '_' + target_obj.name, type='ARRAY')
        mod.count = count
        mod.use_relative_offset = True
        mod.relative_offset_displace = scale_axis
        mod.use_merge_vertices = use_merge_vertices
        mod.use_merge_vertices_cap = use_merge_vertices

        mod2 = target_obj.modifiers.new(name='SIMPLE_DEFORM' + '_' + target_obj.name, type='SIMPLE_DEFORM')
        mod2.deform_axis = deform_axis
        mod2.deform_method = 'BEND'
        mod2.angle = math.radians(angle)

        # get a reference to the current obj.data
        old_mesh = target_obj.data

        (ctx, edp) = capture_context([target_obj])
        object_eval = target_obj.evaluated_get(edp)
        new_mesh_from_eval = bpy.data.meshes.new_from_object(object_eval, preserve_all_data_layers=True, depsgraph=edp)

        # object will still have modifiers, remove them
        target_obj.modifiers.clear()

        # assign the new mesh to obj.data 
        target_obj.data = new_mesh_from_eval

        # remove the old mesh from the .blend
        if old_mesh:
            bpy.data.meshes.remove(old_mesh)

        #origin_set_object(target_obj)
        # clear object location
        target_obj.location -= Vector(displace_axis)
        transform_apply_object([target_obj])

        if use_merge_vertices:
            weld_operator([target_obj])

        if use_local_space:
            target_obj.matrix_basis = matrix_basis

        if delete_interior:
            delete_interior_faces(target_obj)

    return (inputstream, None)


def mirror_operator(inputstream0, inputstream1, options={}):
    use_axis = options['use_axis']
    use_bisect_axis = options['use_bisect_axis']
    use_bisect_flip_axis = options['use_bisect_flip_axis']
    use_clip = options['use_clip']
    use_mirror_merge = options['use_mirror_merge']
    merge_threshold = options['merge_threshold']

    for target_obj in inputstream0:
        mod = target_obj.modifiers.new(name='MIRROR' + '_' + target_obj.name, type='MIRROR')
        mod.use_axis = use_axis
        mod.use_bisect_axis = use_bisect_axis
        mod.use_bisect_flip_axis = use_bisect_flip_axis
        mod.use_clip = use_clip
        mod.use_mirror_merge = use_mirror_merge
        mod.merge_threshold = merge_threshold
        if len(inputstream1) > 0:
            mirror_object = inputstream1[0]
            mod.mirror_object = mirror_object

        # get a reference to the current obj.data
        old_mesh = target_obj.data

        (ctx, edp) = capture_context([target_obj])
        object_eval = target_obj.evaluated_get(edp)
        new_mesh_from_eval = bpy.data.meshes.new_from_object(object_eval, preserve_all_data_layers=True, depsgraph=edp)

        # object will still have modifiers, remove them
        target_obj.modifiers.clear()

        # assign the new mesh to obj.data 
        target_obj.data = new_mesh_from_eval

        # remove the old mesh from the .blend
        if old_mesh:
            bpy.data.meshes.remove(old_mesh)

    return (inputstream0, None)


def subdivide_operator(inputstream, options={}):
    subdivision_type = options['subdivision_type']
    levels = options['levels']
    quality = options['quality']
    use_limit_surface = options['use_limit_surface']
    uv_smooth = options['uv_smooth']
    boundary_smooth = options['boundary_smooth']
    use_creases = options['use_creases']
    use_custom_normals = options['use_custom_normals']

    for target_obj in inputstream:
        mod = target_obj.modifiers.new(name='SUBSURF' + '_' + target_obj.name, type='SUBSURF')
        mod.subdivision_type = subdivision_type
        mod.levels = levels
        # mod.render_levels = 2
        mod.quality = quality
        mod.use_limit_surface = use_limit_surface
        mod.uv_smooth = uv_smooth
        mod.boundary_smooth = boundary_smooth
        mod.use_creases = use_creases
        mod.use_custom_normals = use_custom_normals

        # get a reference to the current obj.data
        old_mesh = target_obj.data

        (ctx, edp) = capture_context([target_obj])
        object_eval = target_obj.evaluated_get(edp)
        new_mesh_from_eval = bpy.data.meshes.new_from_object(object_eval, preserve_all_data_layers=True, depsgraph=edp)

        # object will still have modifiers, remove them
        target_obj.modifiers.clear()

        # assign the new mesh to obj.data 
        target_obj.data = new_mesh_from_eval

        # remove the old mesh from the .blend
        if old_mesh:
            bpy.data.meshes.remove(old_mesh)

    return (inputstream, None)


def triangulate_operator(inputstream, options={}):
    quad_method = options['quad_method']
    ngon_method = options['ngon_method']
    min_vertices = options['min_vertices']
    keep_custom_normals = options['keep_custom_normals']

    for target_obj in inputstream:
        mod = target_obj.modifiers.new(name='TRIANGULATE' + '_' + target_obj.name, type='TRIANGULATE')
        mod.quad_method = quad_method
        mod.ngon_method = ngon_method
        mod.min_vertices = min_vertices
        mod.keep_custom_normals = keep_custom_normals

        # get a reference to the current obj.data
        old_mesh = target_obj.data

        (ctx, edp) = capture_context([target_obj])
        object_eval = target_obj.evaluated_get(edp)
        new_mesh_from_eval = bpy.data.meshes.new_from_object(object_eval, preserve_all_data_layers=True, depsgraph=edp)

        # object will still have modifiers, remove them
        target_obj.modifiers.clear()

        # assign the new mesh to obj.data 
        target_obj.data = new_mesh_from_eval

        # remove the old mesh from the .blend
        if old_mesh:
            bpy.data.meshes.remove(old_mesh)

    return (inputstream, None)

def solidify_operator(inputstream, options={}):
    solidify_mode = options['solidify_mode']
    thickness = options['thickness']
    offset = options['offset']
    use_rim = options['use_rim']
    use_rim_only = options['use_rim_only']

    for target_obj in inputstream:
        mod = target_obj.modifiers.new(name='SOLIDIFY' + '_' + target_obj.name, type='SOLIDIFY')
        mod.solidify_mode = solidify_mode
        mod.thickness = thickness
        mod.offset = offset
        mod.use_rim = use_rim
        mod.use_rim_only = use_rim_only

        # get a reference to the current obj.data
        old_mesh = target_obj.data

        (ctx, edp) = capture_context([target_obj])
        object_eval = target_obj.evaluated_get(edp)
        new_mesh_from_eval = bpy.data.meshes.new_from_object(object_eval, preserve_all_data_layers=True, depsgraph=edp)

        # object will still have modifiers, remove them
        target_obj.modifiers.clear()

        # assign the new mesh to obj.data 
        target_obj.data = new_mesh_from_eval

        # remove the old mesh from the .blend
        if old_mesh:
            bpy.data.meshes.remove(old_mesh)

    return (inputstream, None)


def skin_operator(inputstream, options={}):
    # attribute_name = options['attribute_name']
    scale = options['scale']
    branch_smoothing = options['branch_smoothing']
    mark_root = options['mark_root']
    mark_loose = options['mark_loose']
    use_smooth_shade = options['use_smooth_shade']

    for obj in inputstream:
        me = obj.data
        mod = obj.modifiers.new(name='SKIN' + '_' + obj.name, type='SKIN')
        mod.branch_smoothing = branch_smoothing
        mod.use_x_symmetry = False
        mod.use_y_symmetry = False
        mod.use_z_symmetry = False
        mod.use_smooth_shade = use_smooth_shade

        radii = [scale] * len(me.vertices) * 2
        me.skin_vertices[''].data.foreach_set('radius', radii)

        mark_roots = [mark_root] * len(me.vertices)
        me.skin_vertices[''].data.foreach_set('use_root', mark_roots)

        mark_looses = [mark_loose] * len(me.vertices)
        me.skin_vertices[''].data.foreach_set('use_loose', mark_looses)

        # for vert_index, vert in enumerate(me.vertices):
        #     me.skin_vertices[''].data[vert_index].radius = (scale, scale)

        # get a reference to the current obj.data
        old_mesh = obj.data

        (ctx, edp) = capture_context([obj])
        object_eval = obj.evaluated_get(edp)
        new_mesh_from_eval = bpy.data.meshes.new_from_object(object_eval, preserve_all_data_layers=True, depsgraph=edp)

        # object will still have modifiers, remove them
        obj.modifiers.clear()

        # assign the new mesh to obj.data 
        obj.data = new_mesh_from_eval

        # remove the old mesh from the .blend
        if old_mesh:
            bpy.data.meshes.remove(old_mesh)

    return (inputstream, None)


def screw_operator(inputstream0, inputstream1, options={}):
    angle = options['angle']
    screw_offset = options['screw_offset']
    iterations = options['iterations']
    axis = options['axis']
    axis_object = None
    use_object_screw_offset = options['use_object_screw_offset']
    steps = options['steps']
    use_merge_vertices = options['use_merge_vertices']
    merge_threshold = options['merge_threshold']

    if len(inputstream1) > 0:
        axis_object = inputstream1[0]

    for obj in inputstream0:
        me = obj.data
        mod = obj.modifiers.new(name='SCREW' + '_' + obj.name, type='SCREW')
        mod.angle = math.radians(angle)
        mod.screw_offset = screw_offset
        mod.iterations = iterations
        mod.axis = axis
        mod.object = axis_object
        mod.steps = steps
        mod.use_object_screw_offset = use_object_screw_offset
        mod.use_merge_vertices = use_merge_vertices
        mod.merge_threshold = merge_threshold

        # get a reference to the current obj.data
        old_mesh = obj.data

        (ctx, edp) = capture_context([obj])
        object_eval = obj.evaluated_get(edp)
        new_mesh_from_eval = bpy.data.meshes.new_from_object(object_eval, preserve_all_data_layers=True, depsgraph=edp)

        # object will still have modifiers, remove them
        obj.modifiers.clear()

        # assign the new mesh to obj.data 
        obj.data = new_mesh_from_eval

        # remove the old mesh from the .blend
        if old_mesh:
            bpy.data.meshes.remove(old_mesh)

    return (inputstream0, None)


AXIS_MAP = {
    "X": (1.0,0.0,0.0),
    "Y": (0.0,1.0,0.0),
    "Z": (0.0,0.0,1.0),
}


def bisect_operator(inputstream, options={}):
    axis = AXIS_MAP[options['axis']]
    cuts = options['cuts'] + 1

    for obj in inputstream:
        me = obj.data

        bm = bmesh.new()
        bm.from_mesh(me)

        location = obj.location
        dimensions = obj.dimensions
        cut_size = dimensions / cuts
        start_location = location - dimensions / 2

        for index in range(cuts):
            cut_offset = cut_size @ Matrix.Diagonal(axis) * index
            plane_co = start_location + cut_offset
            bmesh.ops.bisect_plane(bm, geom = bm.edges[:] + bm.faces[:], dist = 0, plane_co = plane_co, plane_no = axis, clear_outer = False, clear_inner = False)

        # put back
        bm.to_mesh(obj.data)
        obj.data.update()
        bm.free()

    return (inputstream, None)


def resample_operator(inputstream, options={}):
    segments = options['segments']
    length = options['length']
    
    for obj in inputstream:
        me = obj.data
        # Get a BMesh representation
        bm = bmesh.new()
        bm.from_mesh(me)

        edge_cuts = [(e, e.calc_length() / length) for e in bm.edges]

        for edge, cuts in edge_cuts:
            bmesh.ops.bisect_edges(bm, edges=[edge], cuts=cuts, edge_percents={edge: 1.0})

        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.000001)
        # bmesh.ops.bisect_edges(bm, edges=edges, cuts=1, edge_percents=edge_percents)
        # # [bmesh.utils.edge_split(edge, edge.verts[0], fac) for edge, fac in edges]

        # Finish up, write the bmesh back to the mesh
        bm.to_mesh(me)
        me.update()
        bm.free()

    return (inputstream, None)


def smooth_operator(inputstream, options={}):
    smooth_type = options['smooth_type']
    repeat = options['repeat']
    factor = options['factor']
    preserve_volume = options['preserve_volume']
    
    for obj in inputstream:
        me = obj.data
        # Get a BMesh representation
        bm = bmesh.new()
        bm.from_mesh(me)

        for idx in range(repeat):
            if smooth_type == 'SIMPLE':
                bmesh.ops.smooth_vert(bm, verts=bm.verts, factor=factor, use_axis_x=True, use_axis_y=True, use_axis_z=True)
            else:
                bmesh.ops.smooth_laplacian_vert(bm, verts=bm.verts, lambda_factor=factor, lambda_border=0.01, preserve_volume=preserve_volume, use_x=True, use_y=True, use_z=True)

        # Finish up, write the bmesh back to the mesh
        bm.to_mesh(me)
        me.update()
        bm.free()

    return (inputstream, None)


def passthrough_operator(*inputstreams, options={}):
    join = options['join']

    objects = []
    for inputstream in inputstreams:
        objects += inputstream

    if join == True:
        (ret, prev) = merge_operator(objects)
        return (ret, prev)
    else:
        return (objects, None)
