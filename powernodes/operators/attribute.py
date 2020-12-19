import bpy
import bmesh
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

from .. parse import attribute_create, attribute_get, evaluate_expression, extract_custom_attribute_layers, evaluate_expression_foreach, TYPE_INITIAL_VALUE


def create_attribute(inputstream, options={}):
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


def evaluate_attribute_expression(inputstream, options={}):
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
    from_domain = options['from_domain']
    to_domain = options['to_domain']
    attribute_name = options['attribute_name']

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

        # Finish up, write the bmesh back to the mesh
        bm.to_mesh(me)
        me.update()
        bm.free()

    return (inputstream, None)
