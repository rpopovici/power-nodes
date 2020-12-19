import bpy
import bmesh
import random

from .. parse import attribute_create, attribute_get, evaluate_expression, extract_custom_attribute_layers, evaluate_expression_foreach, TYPE_INITIAL_VALUE


def sort_by_xyz(inputstream, options={}):
    select_type = options['select_type']
    attribute_name = options['attribute_name']

    for obj in inputstream:
        me = obj.data

        # Get a BMesh representation
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        dims = obj.dimensions
        elements = []
        sort_points = []

        if select_type == 'VERT':
            elements = bm.verts
            sort_points = [(v.index, v.co) for v in bm.verts]
            # _attr_ = (bm.verts.layers.int.get(attribute_name) or bm.verts.layers.int.new(attribute_name))

        if select_type == 'EDGE':
            elements = bm.edges
            sort_points = [(e.index, (e.verts[0].co + e.verts[1].co) / 2) for e in bm.edges]
            # _attr_ = (bm.edges.layers.int.get(attribute_name) or bm.edges.layers.int.new(attribute_name))

        if select_type == 'FACE':
            elements = bm.faces
            sort_points = [(f.index, f.calc_center_median()) for f in bm.faces]
            # _attr_ = (bm.faces.layers.int.get(attribute_name) or bm.faces.layers.int.new(attribute_name))

        custom_attr_layer_items = extract_custom_attribute_layers([attribute_name], me, bm, select_type)
        if len(custom_attr_layer_items) == 0:
            continue

        attr, attr_layer_item, attr_domain, attr_data_type = custom_attr_layer_items[0]
        if attr_data_type != 'INT':
            continue

        def compare(A, B):
            A_val = A[1].z * dims.y * dims.x + A[1].y * dims.x + A[1].x
            B_val = B[1].z * dims.y * dims.x + B[1].y * dims.x + B[1].x
            return A_val < B_val

        sort_points.sort(key=cmp_to_key(compare))

        for index, elem in enumerate(elements):
            elem[attr_layer_item] = sort_points[index][0]  

        # Finish up, write the bmesh back to the mesh
        bm.to_mesh(me)
        me.update()
        bm.free()

    return (inputstream, None)


def sort_by_random(inputstream, options={}):
    select_type = options['select_type']
    attribute_name = options['attribute_name']
    seed = options['seed']

    random.seed(seed)

    for obj in inputstream:
        me = obj.data

        # me.attributes.new(name='id', type='INT', domain='POLYGON')
        # me.attributes[0].data[0].value = 1

        # Get a BMesh representation
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        if select_type == 'VERT':
            elements = bm.verts
            # _attr_ = (bm.verts.layers.int.get(attribute_name) or bm.verts.layers.int.new(attribute_name))

        if select_type == 'EDGE':
            elements = bm.edges
            # _attr_ = (bm.edges.layers.int.get(attribute_name) or bm.edges.layers.int.new(attribute_name))

        if select_type == 'FACE':
            elements = bm.faces
            # _attr_ = (bm.faces.layers.int.get(attribute_name) or bm.faces.layers.int.new(attribute_name))

        custom_attr_layer_items = extract_custom_attribute_layers([attribute_name], me, bm, select_type)
        if len(custom_attr_layer_items) == 0:
            continue

        attr, attr_layer_item, attr_domain, attr_data_type = custom_attr_layer_items[0]
        if attr_data_type != 'INT':
            continue

        for index, elem in enumerate(elements):
            elem_index = elem.index
            rand_index = random.randint(0, len(elements)-1)
            elem.index = elements[rand_index].index
            elements[rand_index].index = elem_index
            elem[attr_layer_item] = elem.index

        # elements.index_update()

        # Finish up, write the bmesh back to the mesh
        bm.to_mesh(me)
        me.update()
        bm.free()

    return (inputstream, None)
