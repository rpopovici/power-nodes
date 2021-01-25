import bpy
import bmesh
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
from mathutils.noise import random, random_vector, random_unit_vector, seed_set
import random

from .. parse import attribute_create, attribute_get, evaluate_expression, extract_custom_attribute_layers, evaluate_expression_foreach, TYPE_INITIAL_VALUE

MAX_INT = 2147483647

def create_attribute_op(inputstream, options={}):
    domain = options['domain']
    attribute_type = options['attribute_type']
    attribute_name = options['attribute_name']
    attr_default_value = options['attr_default_value']

    value = 0
    try:
        if attribute_type == 'INT':
            value_name = 'value'
            value = int(attr_default_value)
        elif attribute_type == 'FLOAT':
            value_name = 'value'
            value = float(attr_default_value)
        elif attribute_type == 'FLOAT_VECTOR':
            value_name = 'vector'
            t = tuple(map(float, attr_default_value.split(',')))
            value = Vector(t)
        elif attribute_type in ['FLOAT_COLOR', 'BYTE_COLOR']:
            value_name = 'color'
            t = tuple(map(float, attr_default_value.split(',')))
            value = t
    except Exception as e:
        print('Failed to determine attribute type: ', str(e))

    for obj in inputstream:
        me = obj.data
        attribute_create(me, attribute_name, domain, attribute_type)
        # me.attributes.new(name=attribute_name, type=attribute_type, domain=domain)
        attribute = attribute_get(me, attribute_name, domain)
        # attribute = me.attributes.get(attribute_name)
        try:
            for attr in attribute.data: setattr(attr, value_name, value)
        except Exception as e:
            print('Failed to initialize attribute: ', str(e))

    return (inputstream, None)


def copy_attribute_op(inputstream0, inputstream1, options={}):
    from_domain = options['from_domain']
    attribute_name = options['attribute_name']

    for from_obj in inputstream1:
        from_me = from_obj.data

        # get data type from from_attr
        from_attr = attribute_get(from_me, attribute_name, from_domain)
        if not from_attr:
            continue

        # Get a BMesh representation
        from_bm = bmesh.new()
        from_bm.from_mesh(from_me)
        from_bm.verts.ensure_lookup_table()
        from_bm.edges.ensure_lookup_table()
        from_bm.faces.ensure_lookup_table()

        for to_obj in inputstream0:
            to_me = to_obj.data
            attribute_create(to_me, attribute_name, from_domain, from_attr.data_type)

            to_bm = bmesh.new()
            to_bm.from_mesh(to_me)
            to_bm.verts.ensure_lookup_table()
            to_bm.edges.ensure_lookup_table()
            to_bm.faces.ensure_lookup_table()

            from_elements = []
            to_elements = []
            if from_domain == 'VERTEX':
                from_elements = from_bm.verts
                to_elements = to_bm.verts
            if from_domain == 'EDGE':
                from_elements = from_bm.edges
                to_elements = to_bm.edges
            if from_domain == 'POLYGON':
                from_elements = from_bm.faces
                to_elements = to_bm.faces
            if from_domain == 'CORNER':
                from_elements = [loop for face in from_bm.faces for loop in face.loops]
                to_elements = [loop for face in to_bm.faces for loop in face.loops]

            from_attr_layer_items = extract_custom_attribute_layers([attribute_name], from_me, from_bm, from_domain)
            to_attr_layer_items = extract_custom_attribute_layers([attribute_name], to_me, to_bm, from_domain)
            _, from_attr_layer_item, _, _ = from_attr_layer_items[0]
            _, to_attr_layer_item, _, _ = to_attr_layer_items[0]
            for from_elem, to_elem in zip(from_elements, to_elements):
                to_elem[to_attr_layer_item] = from_elem[from_attr_layer_item]

            # Finish up, write the bmesh back to the mesh
            to_bm.to_mesh(to_me)
            to_me.update()
            to_bm.free()

        from_bm.free()

    return (inputstream0, None)


def evaluate_attribute_expression_op(inputstream, options={}):
    domain = options['domain']
    attribute_name = options['attribute_name']
    expression = options['expression']

    for obj in inputstream:
        me = obj.data

        # Get a BMesh representation
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        elements = []
        if domain == 'VERTEX':
            elements = bm.verts
        if domain == 'EDGE':
            elements = bm.edges
        if domain == 'POLYGON':
            elements = bm.faces
        if domain == 'CORNER':
            elements = [loop for face in bm.faces for loop in face.loops]

        try:
            custom_attr_layer_items = extract_custom_attribute_layers([attribute_name], me, bm, domain)
            values = evaluate_expression_foreach(elements, expression, obj, me, bm, domain)
            if len(custom_attr_layer_items) == 0:
                for elem, value in zip(elements, values): setattr(elem, attribute_name, value)
            else:
                attr, attr_layer_item, _, _ = custom_attr_layer_items[0]
                for elem, value in zip(elements, values): elem[attr_layer_item] = value
        except Exception as e:
            print('Failed to evaluate expression: ', str(e))

        # Finish up, write the bmesh back to the mesh
        bm.to_mesh(me)
        me.update()
        bm.free()

    return (inputstream, None)


def elevate_attribute_op(inputstream, options={}):
    elevate_mode = options['elevate_mode']
    attribute_name = options['attribute_name']

    from_domain = elevate_mode.split('_TO_')[0]
    to_domain = elevate_mode.split('_TO_')[1]

    for obj in inputstream:
        me = obj.data

        # get data type from from_attr
        from_attr = attribute_get(me, attribute_name, from_domain)
        if not from_attr:
            continue

        attribute_create(me, attribute_name, to_domain, from_attr.data_type)

        # Get a BMesh representation
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        if from_domain == 'CORNER' and to_domain == 'VERTEX':
            from_attr_layer_items = extract_custom_attribute_layers([attribute_name], me, bm, from_domain)
            to_attr_layer_items = extract_custom_attribute_layers([attribute_name], me, bm, to_domain)
            if len(from_attr_layer_items) > 0:
                _, from_attr_layer_item, _, _ = from_attr_layer_items[0]
                _, to_attr_layer_item, _, _ = to_attr_layer_items[0]
                for vert in bm.verts:
                    corner_values = [loop[from_attr_layer_item] for loop in vert.link_loops]
                    average_value = sum(corner_values, TYPE_INITIAL_VALUE[from_attr.data_type]) / len(corner_values)
                    vert[to_attr_layer_item] = average_value

        if from_domain == 'VERTEX' and to_domain == 'CORNER':
            from_attr_layer_items = extract_custom_attribute_layers([attribute_name], me, bm, from_domain)
            to_attr_layer_items = extract_custom_attribute_layers([attribute_name], me, bm, to_domain)
            if len(from_attr_layer_items) > 0:
                _, from_attr_layer_item, _, _ = from_attr_layer_items[0]
                _, to_attr_layer_item, _, _ = to_attr_layer_items[0]
                for vert in bm.verts:
                    for loop in vert.link_loops: loop[to_attr_layer_item] = vert[from_attr_layer_item]

        if from_domain == 'CORNER' and to_domain == 'POLYGON':
            from_attr_layer_items = extract_custom_attribute_layers([attribute_name], me, bm, from_domain)
            to_attr_layer_items = extract_custom_attribute_layers([attribute_name], me, bm, to_domain)
            if len(from_attr_layer_items) > 0:
                _, from_attr_layer_item, _, _ = from_attr_layer_items[0]
                _, to_attr_layer_item, _, _ = to_attr_layer_items[0]
                for face in bm.faces:
                    corner_values = [loop[from_attr_layer_item] for loop in face.loops]
                    average_value = sum(corner_values, TYPE_INITIAL_VALUE[from_attr.data_type]) / len(corner_values)
                    face[to_attr_layer_item] = average_value

        if from_domain == 'POLYGON' and to_domain == 'CORNER':
            from_attr_layer_items = extract_custom_attribute_layers([attribute_name], me, bm, from_domain)
            to_attr_layer_items = extract_custom_attribute_layers([attribute_name], me, bm, to_domain)
            if len(from_attr_layer_items) > 0:
                _, from_attr_layer_item, _, _ = from_attr_layer_items[0]
                _, to_attr_layer_item, _, _ = to_attr_layer_items[0]
                for face in bm.faces:
                    for loop in face.loops: loop[to_attr_layer_item] = face[from_attr_layer_item]

        if from_domain == 'VERTEX' and to_domain == 'POLYGON':
            from_attr_layer_items = extract_custom_attribute_layers([attribute_name], me, bm, from_domain)
            to_attr_layer_items = extract_custom_attribute_layers([attribute_name], me, bm, to_domain)
            if len(from_attr_layer_items) > 0:
                _, from_attr_layer_item, _, _ = from_attr_layer_items[0]
                _, to_attr_layer_item, _, _ = to_attr_layer_items[0]
                for face in bm.faces:
                    vert_values = [vert[from_attr_layer_item] for vert in face.verts]
                    average_value = sum(vert_values, TYPE_INITIAL_VALUE[from_attr.data_type]) / len(vert_values)
                    face[to_attr_layer_item] = average_value

        if from_domain == 'POLYGON' and to_domain == 'VERTEX':
            from_attr_layer_items = extract_custom_attribute_layers([attribute_name], me, bm, from_domain)
            to_attr_layer_items = extract_custom_attribute_layers([attribute_name], me, bm, to_domain)
            if len(from_attr_layer_items) > 0:
                _, from_attr_layer_item, _, _ = from_attr_layer_items[0]
                _, to_attr_layer_item, _, _ = to_attr_layer_items[0]
                for face in bm.faces:
                    for vert in face.verts: vert[to_attr_layer_item] = face[from_attr_layer_item]

        # Finish up, write the bmesh back to the mesh
        bm.to_mesh(me)
        me.update()
        bm.free()

    return (inputstream, None)


def transport_attribute_op(inputstream0, inputstream1, options={}):
    from_domain = options['from_domain']
    attribute_name = options['attribute_name']
    distance = options['distance']

    for from_obj in inputstream1:
        from_me = from_obj.data

        # get data type from from_attr
        from_attr = attribute_get(from_me, attribute_name, from_domain)
        if not from_attr:
            continue

        # Get a BMesh representation
        from_bm = bmesh.new()
        from_bm.from_mesh(from_me)
        from_bm.verts.ensure_lookup_table()
        from_bm.edges.ensure_lookup_table()
        from_bm.faces.ensure_lookup_table()

        bhv_tree = BVHTree.FromBMesh(from_bm, epsilon=0.00001)

        for to_obj in inputstream0:
            to_me = to_obj.data
            attribute_create(to_me, attribute_name, from_domain, from_attr.data_type)

            to_bm = bmesh.new()
            to_bm.from_mesh(to_me)
            to_bm.verts.ensure_lookup_table()
            to_bm.edges.ensure_lookup_table()
            to_bm.faces.ensure_lookup_table()

            from_elements = []
            to_elements = []
            if from_domain == 'VERTEX':
                from_elements = from_bm.verts
                to_elements = to_bm.verts
            if from_domain == 'EDGE':
                from_elements = from_bm.edges
                to_elements = to_bm.edges
            if from_domain == 'POLYGON':
                from_elements = from_bm.faces
                to_elements = to_bm.faces
            if from_domain == 'CORNER':
                from_elements = [loop for face in from_bm.faces for loop in face.loops]
                to_elements = [loop for face in to_bm.faces for loop in face.loops]

            from_attr_layer_items = extract_custom_attribute_layers([attribute_name], from_me, from_bm, from_domain)
            to_attr_layer_items = extract_custom_attribute_layers([attribute_name], to_me, to_bm, from_domain)
            _, from_attr_layer_item, _, _ = from_attr_layer_items[0]
            _, to_attr_layer_item, _, _ = to_attr_layer_items[0]

            bvh_find_nearest = bhv_tree.find_nearest

            if from_domain == 'VERTEX':
                for to_index, vert in enumerate(to_bm.verts):
                    (loc, norm, from_index, dist) = bvh_find_nearest(vert.co, distance)
                    if from_index:
                        for face_vert in from_bm.faces[from_index].verts:
                            if (vert.co - face_vert.co).length <= distance:
                                from_elem = face_vert
                                to_elem = to_elements[to_index]
                                to_elem[to_attr_layer_item] = from_elem[from_attr_layer_item]
                                break

            if from_domain == 'POLYGON':
                for to_index, face in enumerate(to_bm.faces):
                    (loc, norm, from_index, dist) = bvh_find_nearest(face.calc_center_median(), distance)
                    if from_index:
                        from_elem = from_elements[from_index]
                        to_elem = to_elements[to_index]
                        to_elem[to_attr_layer_item] = from_elem[from_attr_layer_item]

            # Finish up, write the bmesh back to the mesh
            to_bm.to_mesh(to_me)
            to_me.update()
            to_bm.free()

        from_bm.free()

    return (inputstream0, None)


def randomize_attribute_op(inputstream, options={}):
    domain = options['domain']
    attribute_name = options['attribute_name']
    seed = options['seed']

    for index, obj in enumerate(inputstream):
        me = obj.data

        # get data type from attribute
        attribute = attribute_get(me, attribute_name, domain)
        if not attribute:
            continue

        seed_set(seed + index)

        # Get a BMesh representation
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        elements = []
        if domain == 'VERTEX':
            elements = bm.verts
        if domain == 'EDGE':
            elements = bm.edges
        if domain == 'POLYGON':
            elements = bm.faces
        if domain == 'CORNER':
            elements = [loop for face in bm.faces for loop in face.loops]

        custom_attr_layer_items = extract_custom_attribute_layers([attribute_name], me, bm, domain)
        attr, attr_layer_item, _, _ = custom_attr_layer_items[0]

        if attribute.data_type in ['INT']:
            random.seed(seed + index)
            for elem in elements: elem[attr_layer_item] = random.randint(0, MAX_INT)

        if attribute.data_type in ['FLOAT']:
            for elem in elements: elem[attr_layer_item] = random()

        if attribute.data_type in ['FLOAT_VECTOR']:
            for elem in elements: elem[attr_layer_item] = random_vector(size=3)

        if attribute.data_type in ['FLOAT_COLOR']:
            for elem in elements: elem[attr_layer_item] = random_unit_vector(size=4)

        if attribute.data_type in ['BYTE_COLOR']:
            for elem in elements: elem[attr_layer_item] = random_unit_vector(size=4) * 255

        # Finish up, write the bmesh back to the mesh
        bm.to_mesh(me)
        me.update()
        bm.free()

    return (inputstream, None)
