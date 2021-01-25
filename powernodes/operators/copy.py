import bpy
import bmesh
from mathutils import Vector, Matrix

from .. ops import origin_to_center, origin_to_bottom, transform_apply_object
from .. parse import attribute_create, attribute_get, evaluate_expression, extract_custom_attribute_layers, evaluate_expression_foreach, TYPE_INITIAL_VALUE


def calc_transform_matrix(bound_box, target_pos, target_normal, align_type, normal_align):
    copy_loc = Matrix.Translation(target_pos)
    copy_quat = target_normal.to_track_quat("Z", "X")
    copy_rot = copy_quat.to_matrix().to_4x4()
    copy_mat = Matrix()

    copy_mat = copy_loc

    if normal_align:
        copy_mat = copy_loc @ copy_rot

    if align_type == 'CENTER':
        org = origin_to_center(bound_box)
        copy_mat = copy_mat @ Matrix.Translation(-org)

    if align_type == 'BOTTOM':
        org = origin_to_bottom(bound_box)
        copy_mat = copy_mat @ Matrix.Translation(-org)

    return copy_mat


def copy_operator(inputstream0, inputstream1, options={}):
    select_type = options['select_type']
    expression = options['expression']
    normal_align = options['normal_align']
    align_type = options['align_type']
    edge_normal = options['edge_normal']
    use_instance = options['use_instance']

    if use_instance == True:
        instances = []
        for target_obj in inputstream1:
            transform_apply_object([target_obj])

            target_bm = bmesh.new()
            target_bm.from_mesh(target_obj.data)

            elements = []
            if select_type == 'VERT':
                elements = target_bm.verts
                mesh_elements = target_obj.data.vertices
            if select_type == 'EDGE':
                elements = target_bm.edges
                mesh_elements = target_obj.data.edges
            if select_type == 'FACE':
                elements = target_bm.faces
                mesh_elements = target_obj.data.polygons

            try:
                values = evaluate_expression_foreach(elements, expression, target_obj, target_obj.data, target_bm, select_type, default_ret=True)
                for elem, value in zip(mesh_elements, values): setattr(elem, 'select', bool(value))
                # target_bm.select_flush(False)
            except Exception as e:
                print('Failed to evaluate expression: ', str(e))

            for select_obj in inputstream0:
                select_instances = []
                transform_apply_object([select_obj])

                if select_type == 'VERT':
                    for target_vert in target_obj.data.vertices:
                        if not target_vert.select:
                            continue

                        copy_mat_world = select_obj.matrix_world
                        copy_mat = calc_transform_matrix(select_obj.bound_box, target_vert.co, target_vert.normal, align_type, normal_align)
                        copy_mat = copy_mat_world @ copy_mat

                        new_object = bpy.data.objects.new(select_obj.name + '_COPY', select_obj.data)
                        new_object.matrix_world = copy_mat
                        select_instances.append(new_object)

                instances.extend(select_instances)

            target_bm.free()

        return (instances, None)


    for target_obj in inputstream1:
        transform_apply_object([target_obj])

        target_bm = bmesh.new()
        target_bm.from_mesh(target_obj.data)

        elements = []
        if select_type == 'VERT':
            elements = target_bm.verts
            mesh_elements = target_obj.data.vertices
        if select_type == 'EDGE':
            elements = target_bm.edges
            mesh_elements = target_obj.data.edges
        if select_type == 'FACE':
            elements = target_bm.faces
            mesh_elements = target_obj.data.polygons

        try:
            values = evaluate_expression_foreach(elements, expression, target_obj, target_obj.data, target_bm, select_type, default_ret=True)
            for elem, value in zip(mesh_elements, values): setattr(elem, 'select', bool(value))
            # target_bm.select_flush(False)
        except Exception as e:
            print('Failed to evaluate expression: ', str(e))


        for select_obj in inputstream0:
            transform_apply_object([select_obj])

            bm = bmesh.new()

            if select_type == 'VERT':
                for target_vert in target_obj.data.vertices:
                    if not target_vert.select:
                        continue

                    mesh_copy = select_obj.data.copy()

                    copy_mat_world = select_obj.matrix_world
                    copy_mat = calc_transform_matrix(select_obj.bound_box, target_vert.co, target_vert.normal, align_type, normal_align)
                    copy_mat = copy_mat_world @ copy_mat

                    mesh_copy.transform(copy_mat)
                    # for vert_copy in mesh_copy.vertices:
                    #     vert_copy.co = copy_mat @ vert_copy.co

                    # merge meshes to bm
                    bm.from_mesh(mesh_copy)
                    # remove mesh copies
                    bpy.data.meshes.remove(mesh_copy)

            if select_type == 'EDGE':
                for target_edge in target_obj.data.edges:
                    if not target_edge.select:
                        continue

                    mesh_copy = select_obj.data.copy()
                    
                    vert0 = target_obj.data.vertices[target_edge.vertices[0]]
                    vert1 = target_obj.data.vertices[target_edge.vertices[1]]
                    center = (vert0.co + vert1.co) / 2
                    normal = Vector((0.0, 0.0, 1.0))
                    if edge_normal:
                        normal = (vert1.co - vert0.co).normalized()
                    else:
                        normal = (vert0.normal + vert1.normal) / 2

                    copy_mat_world = select_obj.matrix_world
                    copy_mat = calc_transform_matrix(select_obj.bound_box, center, normal, align_type, normal_align)
                    copy_mat = copy_mat_world @ copy_mat

                    mesh_copy.transform(copy_mat)
                    # for vert_copy in mesh_copy.vertices:
                    #     vert_copy.co = copy_mat @ vert_copy.co

                    # merge meshes to bm
                    bm.from_mesh(mesh_copy)
                    # remove mesh copies
                    bpy.data.meshes.remove(mesh_copy)

            if select_type == 'FACE':
                for target_face in target_obj.data.polygons:
                    if not target_face.select:
                        continue

                    mesh_copy = select_obj.data.copy()
                    
                    copy_mat_world = select_obj.matrix_world
                    copy_mat = calc_transform_matrix(select_obj.bound_box, target_face.center, target_face.normal, align_type, normal_align)
                    copy_mat = copy_mat_world @ copy_mat

                    mesh_copy.transform(copy_mat)
                    # for vert_copy in mesh_copy.vertices:
                    #     vert_copy.co = copy_mat @ vert_copy.co

                    # merge meshes to bm
                    bm.from_mesh(mesh_copy)
                    # remove mesh copies
                    bpy.data.meshes.remove(mesh_copy)

            bm.to_mesh(select_obj.data)
            select_obj.data.update()
            bm.free()

        target_bm.free()


    return (inputstream0, None)
