import bpy
import bmesh

from .. parse import attribute_create, attribute_get, evaluate_expression, extract_custom_attribute_layers, evaluate_expression_foreach, TYPE_INITIAL_VALUE


def delete_operator(inputstream, options={}):
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
        if select_type == 'FACES_ONLY':
            elements = bm.faces
        if select_type == 'FACES_KEEP_BOUNDARY':
            elements = bm.faces

        selected_elements = []
        try:
            values = evaluate_expression_foreach(elements, expression, obj, me, bm, select_type, default_ret=True)
            selected_elements = [elem for elem, value in zip(elements, values) if bool(value)]
        except Exception as e:
            print('Failed to evaluate expression: ', str(e))

        bmesh.ops.delete(bm, geom=selected_elements, context=select_type)

        # Finish up, write the bmesh back to the mesh
        bm.to_mesh(me)
        me.update()
        bm.free()

    return (inputstream, None)


def dissolve_operator(inputstream, options={}):
    select_type = options['select_type']
    expression = options['expression']
    use_face_split = options['use_face_split']
    use_boundary_tear = options['use_boundary_tear']
    use_verts = options['use_verts']

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
            values = evaluate_expression_foreach(elements, expression, obj, me, bm, select_type, default_ret=True)
            selected_elements = [elem for elem, value in zip(elements, values) if bool(value)]
        except Exception as e:
            print('Failed to evaluate expression: ', str(e))

        if select_type == 'VERTS':
            bmesh.ops.dissolve_verts(bm, verts=selected_elements, use_face_split=use_face_split, use_boundary_tear=use_boundary_tear)
        if select_type == 'EDGES':
            bmesh.ops.dissolve_edges(bm, edges=selected_elements, use_verts=use_verts, use_face_split=use_face_split)
        if select_type == 'FACES':
            bmesh.ops.dissolve_faces(bm, faces=selected_elements, use_verts=use_verts)

        # Finish up, write the bmesh back to the mesh
        bm.to_mesh(me)
        me.update()
        bm.free()

    return (inputstream, None)
