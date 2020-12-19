import bpy
import bmesh

from .. parse import attribute_create, attribute_get, evaluate_expression, extract_custom_attribute_layers, evaluate_expression_foreach, TYPE_INITIAL_VALUE


def fill_operator(inputstream, options={}):
    select_type = options['select_type']
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
        if select_type == 'VERTS':
            elements = bm.verts
        if select_type == 'EDGES':
            elements = bm.edges
        if select_type == 'FACES':
            elements = bm.faces

        selected_elements = []
        try:
            values = evaluate_expression_foreach(elements, expression, obj, me, bm, select_type)
            selected_elements = [elem for elem, value in zip(elements, values) if bool(value)]
        except Exception as e:
            print('Failed to evaluate expression: ', str(e))

        bmesh.ops.contextual_create(bm, geom=selected_elements) #, mat_nr, use_smooth)

        # Finish up, write the bmesh back to the mesh
        bm.to_mesh(me)
        me.update()
        bm.free()

    return (inputstream, None)
