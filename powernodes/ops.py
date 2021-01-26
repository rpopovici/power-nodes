import bpy
from bpy_extras.mesh_utils import triangle_random_points
import bmesh
import math
from mathutils import Vector, Matrix
from mathutils.geometry import intersect_line_plane, distance_point_to_plane, intersect_point_line
from mathutils.bvhtree import BVHTree
from mathutils.noise import noise_vector, hetero_terrain, hybrid_multi_fractal, random_vector, seed_set
from math import radians, sqrt
import random

from . parse import attribute_create, attribute_get, evaluate_expression, extract_custom_attribute_layers, evaluate_expression_foreach, TYPE_INITIAL_VALUE
from . utils.utils import calc_bbox_center, matrix_make_positive, curve_length, collinear, timer_start, timer_end

from functools import reduce

import numpy as np


def initialize_default_collections():
    # add default collections if they don't exist
    new_collection('POWER_NODES')
    new_collection('SHADOW_NODES')

    # exclude shadow collection from view layer
    for view_layer in bpy.context.scene.view_layers:
        for layer_collection in view_layer.layer_collection.children:
            if layer_collection.collection.name == 'SHADOW_NODES':
                # layer_collection.exclude = True
                layer_collection.hide_viewport = True
            else:
                # layer_collection.exclude = False
                layer_collection.hide_viewport = False


def capture_context(objects=[]):
    for obj in objects:
        link_to_collection(obj, 'SHADOW_NODES')

    ctx = {} # bpy.context.copy() crashes in 2.91
    # ctx['mode'] = bpy.context.mode
    # ctx['active_operator'] = bpy.context.active_operator
    # ctx['edit_object'] = bpy.context.edit_object
    # # ctx['editable_objects'] = bpy.context.editable_objects
    # ctx['objects_in_mode'] = bpy.context.objects_in_mode
    # ctx['objects_in_mode_unique_data'] = bpy.context.objects_in_mode_unique_data
    # ctx['object'] = bpy.context.object
    # ctx['active_object'] = bpy.context.active_object
    # # ctx['selectable_objects'] = bpy.context.selectable_objects
    # ctx['selected_objects'] = bpy.context.selected_objects
    # # ctx['selected_editable_objects'] = bpy.context.selected_editable_objects
    # ctx['area'] = bpy.context.area
    # ctx['region'] = bpy.context.region
    # ctx['screen'] = bpy.context.screen
    # ctx['view_layer'] = bpy.context.view_layer
    # ctx['window'] = bpy.context.window
    edp = bpy.context.evaluated_depsgraph_get()

    for obj in objects:
        unlink_from_collection(obj, 'SHADOW_NODES')

    # window = bpy.context.window_manager.windows[0]
    # ctx['window'] = window
    # ctx['screen'] = window.screen

    return (ctx, edp)


def new_collection(collection='POWER_NODES'):
    if collection not in bpy.data.collections:
        new_col = bpy.data.collections.new(collection)
        new_col['_pn_tag_'] = True
        bpy.context.scene.collection.children.link(new_col)

    return collection


def link_to_collection(obj=None, collection='POWER_NODES'):
    try:
        # link to collection if not already linked
        if obj.name not in bpy.data.collections[collection].objects:
            bpy.data.collections[collection].objects.link(obj)
    except Exception as e:
        # recreate if missing
        new_collection(collection)
        # try to link again
        if obj.name not in bpy.data.collections[collection].objects:
            bpy.data.collections[collection].objects.link(obj)

    return collection


def unlink_from_collection(obj=None, collection='POWER_NODES'):
    if obj.name in bpy.data.collections[collection].objects:
        bpy.data.collections[collection].objects.unlink(obj)

    return collection


def new_object(name='OUTPUT'):
    empty_mesh = bpy.data.meshes.new('EMPTY_MESH')

    new_obj = bpy.data.objects.new(name, empty_mesh)

    # assign material
    # mat = bpy.data.materials.get("Material")
    # new_obj.data.materials.append(mat)

    return new_obj


def clone_object(obj = None, name='OUTPUT'):
    # copy without selection and view layer overhead
    # new_obj = obj.copy()
    # new_obj.name = name
    new_obj = new_object(name)

    if obj.pn_original:
        new_obj.pn_original = obj.pn_original
    else:
        new_obj.pn_original = obj

    # new_obj.location = obj.location.copy()
    # new_obj.rotation_axis_angle = obj.rotation_axis_angle
    # new_obj.rotation_mode = obj.rotation_mode
    # new_obj.rotation_euler = obj.rotation_euler.copy()
    # new_obj.rotation_quaternion = obj.rotation_quaternion.copy()
    # new_obj.scale = obj.scale.copy()

    # don't set dimensions
    #new_obj.dimensions = obj.dimensions.copy()

    new_obj.color = obj.color

    # try to set the matrices in reverse order
    # new_obj.matrix_world = obj.matrix_world.copy()
    new_obj.matrix_parent_inverse = obj.matrix_parent_inverse.copy()
    new_obj.matrix_local = obj.matrix_local.copy()
    new_obj.matrix_basis = obj.matrix_basis.copy()

    if obj.data:
        # get a reference to the current obj.data
        old_mesh = new_obj.data

        # Invoke new_from_object() for evaluated object.
        (ctx, edp) = capture_context([obj])
        object_eval = obj.evaluated_get(edp)
        mesh_from_eval = bpy.data.meshes.new_from_object(object_eval, preserve_all_data_layers=True, depsgraph=edp)

        # first, remove modifiers
        new_obj.modifiers.clear()

        # copy data from input node
        new_obj.data = mesh_from_eval

        # new_obj.data = src_obj.data.copy()
        # new_obj.data.update()

        # action = ob.animation_data.action
        # # make it a copy
        # ob.animation_data.action = action.copy()

        # remove the old mesh from the .blend
        if old_mesh:
            bpy.data.meshes.remove(old_mesh)

    # #make it None (no action assigned)
    # ob.animation_data.action = None
    # ob.animation_data_clear()
    # ob.modifiers.clear()
    # ob.constraints.clear()

    return new_obj


def clear_object(obj=None):
    if obj and obj.data:
        obj.data.clear_geometry()
        return True

    return False

    #old_mesh = obj.data
    # Remove temporary mesh
    #obj.to_mesh_clear()

    # empty_mesh = bpy.data.meshes.new('EMPTY_MESH')
    # obj.data = empty_mesh

    # remove the old mesh from the .blend
    # bpy.data.meshes.remove(old_mesh)

    #bpy.data.meshes.remove(block)
    # use this in b2.81


def delete_object(obj=None):
    if not obj:
        return False

    # remove
    #objects = [obj]
    #bpy.ops.object.delete({"selected_objects": objects})

    objects = bpy.data.objects
    mesh = obj.data
    objects.remove(obj, do_unlink=True)
    if mesh and mesh.users == 0:
        bpy.data.meshes.remove(mesh)

    return True


def make_active(obj=None):
    bpy.data.objects[obj.name].select_set(True)
    bpy.context.view_layer.objects.active = obj

    return obj


def clear_unused_data():
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)

    for block in bpy.data.materials:
        if block.users == 0:
            bpy.data.materials.remove(block)

    for block in bpy.data.textures:
        if block.users == 0:
            bpy.data.textures.remove(block)

    for block in bpy.data.images:
        if block.users == 0:
            bpy.data.images.remove(block)

    # also have data blocks
    # bpy.data.curves
    # bpy.data.lamps
    # bpy.data.cameras


def origin_to_bottom(bound_box, matrix=Matrix()):
    local_verts = [matrix @ Vector(v[:]) for v in bound_box]
    org = sum(local_verts, Vector()) / 8
    org.z = min(v.z for v in local_verts)
    org = matrix.inverted() @ org

    return org


def origin_to_center(bound_box, matrix=Matrix()):
    local_verts = [matrix @ Vector(v[:]) for v in bound_box]
    org = sum(local_verts, Vector()) / 8
    org = matrix.inverted() @ org

    return org


def fix_t_junction(obj, options={'distance': 0.000001}):
    dist_limit = options['distance']
    # targer from geometry
    bm = bmesh.new()
    bm.from_mesh(obj.data)

    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=options['distance'])

    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    bm.edges.ensure_lookup_table()

    edge_list = []
    fac_list = []

    for edge in bm.edges:
        if not edge.is_boundary: #edge.is_manifold:
            continue
        for edge_vert in edge.verts:
            for link_edge in edge_vert.link_edges: #edge.verts[0].link_edges: # chose only one end
                if edge.tag or link_edge.tag:
                    continue
                e1_dir = edge.verts[1].co - edge.verts[0].co
                e2_dir = link_edge.verts[1].co - link_edge.verts[0].co
                angle = e1_dir.angle(e2_dir)
                if collinear(e1_dir, e2_dir, 0.0001):
                    for vert in link_edge.verts:
                    # vert = link_edge.verts[0] # it should be always vert zero
                        if vert not in edge.verts:
                            (v, fac) = intersect_point_line(vert.co, edge.verts[0].co, edge.verts[1].co)
                            dist = (vert.co - v).length
                            if (dist < dist_limit) and (fac > 0.00001) and (fac < 0.9999):
                                if not edge.tag: #edge.index not in edge_list:
                                    edge.tag = True
                                    #edge_list[edge.index] = fac
                                    edge_list.append((edge.index, fac))
                                    #fac_list.append(fac)

    # edges = [(bm.edges[index], fac) for index, fac in edge_list]
    edges = [bm.edges[index] for index, fac in edge_list]
    edge_percents = {bm.edges[index]: fac for index, fac in edge_list}
    # for edge, fac in edges:
    #     (new_edge, vert) = bmesh.utils.edge_split(edge, edge.verts[0], fac)

    bmesh.ops.bisect_edges(bm, edges=edges, cuts=1, edge_percents=edge_percents)
    # [bmesh.utils.edge_split(edge, edge.verts[0], fac) for edge, fac in edges]

    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=options['distance'])

    # put back
    bm.to_mesh(obj.data)
    obj.data.update()
    bm.free()


def dissolve_tess_edges(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)

    edge_set = set()
    for edge in bm.edges:
        if edge.is_boundary:
            continue
        material_index0 = edge.link_faces[0].material_index
        material_index1 = edge.link_faces[1].material_index

        if material_index0 == material_index1:
            edge_set.add(edge)

    bmesh.ops.dissolve_edges(bm, edges=list(edge_set), use_verts=True, use_face_split=False)

    # put back
    bm.to_mesh(obj.data)
    obj.data.update()
    bm.free()


def merge_operator(inputstream):
    if not inputstream or (len(inputstream) < 2):
        return (inputstream, None)

    # obj = objects[0]
    # (ctx, edp) = capture_context(objects)
    # ctx['object'] = obj
    # ctx['active_object'] = obj
    # ctx['selected_objects'] = objects
    # ctx['selected_editable_objects'] = objects

    # bpy.ops.object.join(ctx)

    # return (objects, None)

    target_obj = inputstream[0]

    bm = bmesh.new()
    for obj in inputstream:
        transform_apply_object([obj])
        bm.from_mesh(obj.data)

    bm.to_mesh(target_obj.data)
    target_obj.data.update()
    bm.free()

    return ([target_obj], None)


def transform_apply_object(inputstream):
    for obj in inputstream:
        # matrix_local = matrix_parent_inverse @ matrix_basis
        # matrix_world = parent.matrix_world @ matrix_local
        # transform the mesh using the matrix world
        obj.data.transform(obj.matrix_basis)

        # then reset matrix to identity
        obj.matrix_world = Matrix()
        # return (objects, None)

        # (ctx, edp) = capture_context(objects)
        # # force object mode context if in edit mode
        # ctx['mode'] = 'OBJECT'
        # ctx['edit_object'] = None
        # ctx['objects_in_mode'] = []
        # ctx['objects_in_mode_unique_data'] = []
        # # choose objects to be transformed
        # ctx['object'] = obj
        # ctx['active_object'] = obj
        # ctx['selected_objects'] = [obj]
        # ctx['selected_editable_objects'] = [obj]

        # bpy.ops.object.transform_apply(ctx, location = True, scale = True, rotation = True)

    return (inputstream, None)


def origin_set_object(inputstream):
    for obj in inputstream:
        local_bbox_center = calc_bbox_center(obj)
        # global_bbox_center = obj.matrix_world * local_bbox_center

        new_origin = local_bbox_center

        obj.data.transform(mathutils.Matrix.Translation(-new_origin))
        obj.location += new_origin
        # obj.matrix_world.translation += new_origin
        # return (objects, None)

        # (ctx, edp) = capture_context(objects)
        # # force object mode context if in edit mode
        # ctx['mode'] = 'OBJECT'
        # ctx['edit_object'] = None
        # ctx['objects_in_mode'] = []
        # ctx['objects_in_mode_unique_data'] = []
        # # # choose objects to be transformed
        # ctx['object'] = obj
        # ctx['active_object'] = obj
        # ctx['selected_objects'] = [obj]
        # ctx['selected_editable_objects'] = [obj]

        # bpy.ops.object.origin_set(ctx, type='ORIGIN_GEOMETRY', center='MEDIAN') # BOUNDS

    return (inputstream, None)


def location_clear_object(inputstream):
    for obj in inputstream:
        # clear location
        obj.location = Vector(0, 0, 0)
        # return (objects, None)

        # (ctx, edp) = capture_context([obj])
        # # force object mode context if in edit mode
        # ctx['mode'] = 'OBJECT'
        # ctx['edit_object'] = None
        # ctx['objects_in_mode'] = []
        # ctx['objects_in_mode_unique_data'] = []
        # # # choose objects to be transformed
        # ctx['object'] = obj
        # ctx['active_object'] = obj
        # ctx['selected_objects'] = [obj]
        # ctx['selected_editable_objects'] = [obj]

        # bpy.ops.object.location_clear(ctx, clear_delta=False)

    return (inputstream, None)


def edge_subdivide_operator(obj):
    me = obj.data
    # Get a BMesh representation
    bm = bmesh.new()
    bm.from_mesh(me)

    bmesh.ops.subdivide_edges(bm,
            edges=bm.edges,
            use_grid_fill=True,
            cuts=1)

    # Finish up, write the bmesh back to the mesh
    bm.to_mesh(me)
    me.update()
    bm.free()


def connect_concave_bmesh_operator(obj):
    me = obj.data
    # Get a BMesh representation
    bm = bmesh.new()
    bm.from_mesh(me)

    for face in bm.faces:
        face.material_index = face.index

    res = bmesh.ops.connect_verts_concave(bm, faces=bm.faces[:])

    # Finish up, write the bmesh back to the mesh
    bm.to_mesh(me)
    me.update()
    bm.free()


def triangulate_bmesh_operator(obj):
    me = obj.data
    # Get a BMesh representation
    bm = bmesh.new()
    bm.from_mesh(me)

    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method="BEAUTY", ngon_method="BEAUTY")

    # Finish up, write the bmesh back to the mesh
    bm.to_mesh(me)
    me.update()
    bm.free()


def quadify_bmesh_operator(obj):
    me = obj.data
    # Get a BMesh representation
    bm = bmesh.new()
    bm.from_mesh(me)

    faces = bmesh.ops.join_triangles(bm, faces=bm.faces[:])

    # Finish up, write the bmesh back to the mesh
    bm.to_mesh(me)
    me.update()
    bm.free()


def delete_interior_faces(obj):
    me = obj.data
    # Get a BMesh representation
    bm = bmesh.new()
    bm.from_mesh(me)

    if hasattr(bm.verts, "ensure_lookup_table"):
        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

    inside_faces = []
    for face in bm.faces:
        if face.hide:
            continue

        is_inside = True
        for edge in face.edges:
            if len(edge.link_faces) < 3:
                is_inside = False
                break

        if is_inside:
            inside_faces.append(face)
            #face.select_set(True)

    # inside_faces = [f for f in bm.faces if not f.hide and reduce(lambda acc, e: acc and len(e.link_faces) > 2, f.edges, True)]

    bmesh.ops.delete(bm, geom=inside_faces, context='FACES')

    # Finish up, write the bmesh back to the mesh
    bm.to_mesh(me)
    me.update()
    bm.free()


def limited_dissolve_bmesh_operator(obj):
    me = obj.data
    # Get a BMesh representation
    bm = bmesh.new()
    bm.from_mesh(me)

    bmesh.ops.dissolve_limit(bm, angle_limit=radians(0.1), use_dissolve_boundaries=True, delimit={'MATERIAL'}, verts=bm.verts, edges=bm.edges)

    # Finish up, write the bmesh back to the mesh
    bm.to_mesh(me)
    me.update()
    bm.free()


def shade_smooth_operator(inputstream, options={}):
    for obj in inputstream:
        mesh = obj.data
        values = [True] * len(mesh.polygons)
        mesh.polygons.foreach_set("use_smooth", values)

    return (inputstream, None)


def create_point_cloud(name='POINTS', options={'coords': [], 'edges': [], 'faces': []}):
    obj = new_object(name=name)
    me = obj.data
    me.clear_geometry()

    coords = options['coords']
    edges = options['edges']
    faces = options['faces']

    me.from_pydata(coords, edges, faces)
    me.update()

    return (obj, None)
