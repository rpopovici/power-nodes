import bpy
import bmesh
from math import degrees, radians

from .. parse import attribute_create, attribute_get, evaluate_expression, extract_custom_attribute_layers, evaluate_expression_foreach, TYPE_INITIAL_VALUE
from .. utils.utils import timer_start, timer_end


def select_by_angle(inputstream, options={}):
    select_type = options['select_type']
    min_angle = options['min_angle']
    max_angle = options['max_angle']

    for obj in inputstream:
        me = obj.data

        # Get a BMesh representation
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        edges = []
        for edge in bm.edges:
            if not edge.is_boundary:
                deg_edge_angle = 180.0 - degrees(edge.calc_face_angle_signed(0.0))
                if deg_edge_angle > min_angle and deg_edge_angle < max_angle:
                    edges.append(edge)

        if select_type == 'VERT':
            for edge in edges:
                for vert in edge.verts:
                    vert.select_set(True)
        if select_type == 'EDGE':
            for edge in edges:
                edge.select_set(True)
        if select_type == 'FACE':
            for edge in edges:
                for face in edge.link_faces:
                    face.select_set(True)

        # Finish up, write the bmesh back to the mesh
        bm.select_flush(False)
        bm.to_mesh(me)
        me.update()
        bm.free()

    return (inputstream, None)


def select_by_boundary(inputstream, options={}):
    select_type = options['select_type']

    for obj in inputstream:
        me = obj.data

        # Get a BMesh representation
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        edges = [edge for edge in bm.edges if edge.is_boundary]

        if select_type == 'VERT':
            for edge in edges:
                for vert in edge.verts:
                    vert.select_set(True)
        if select_type == 'EDGE':
            for edge in edges:
                edge.select_set(True)
        if select_type == 'FACE':
            for edge in edges:
                for face in edge.link_faces:
                    face.select_set(True)

        # Finish up, write the bmesh back to the mesh
        bm.select_flush(False)
        bm.to_mesh(me)
        me.update()
        bm.free()

    return (inputstream, None)


def select_by_bbox(inputstream, options={}):
    center = options['center']
    diagonal = options['diagonal']

    for obj in inputstream:
        me = obj.data

        min_x = center.x - diagonal.x
        max_x = center.x + diagonal.x
        min_y = center.y - diagonal.y
        max_y = center.y + diagonal.y
        min_z = center.z - diagonal.z
        max_z = center.z + diagonal.z

        for vert in me.vertices:
            if (vert.co.x >= min_x and vert.co.x <= max_x and
                vert.co.y >= min_y and vert.co.y <= max_y and
                vert.co.z >= min_z and vert.co.z <= max_z):
                vert.select = True

    return (inputstream, None)


def select_by_index(inputstream, options={}):
    select_type = options['select_type']
    indices_str = options['indices']

    for obj in inputstream:
        me = obj.data

        # reset selection
        values = [False] * len(me.vertices)
        me.vertices.foreach_set("select", values)
        values = [False] * len(me.edges)
        me.edges.foreach_set("select", values)
        values = [False] * len(me.polygons)
        me.polygons.foreach_set("select", values)

        # Get a BMesh representation
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        indices = [int(i) for i in indices_str.split()]

        if len(indices) == 0:
            return (inputstream, None)

        if select_type == 'VERT':
            for index in indices:
                bm.verts[index].select_set(True)

        if select_type == 'EDGE':
            for index in indices:
                bm.edges[index].select_set(True)

        if select_type == 'FACE':
            for index in indices:
                bm.faces[index].select_set(True)

        # Finish up, write the bmesh back to the mesh
        bm.select_flush(False)
        bm.to_mesh(me)
        me.update()
        bm.free()

    return (inputstream, None)


def select_clear(inputstream, options={}):
    for obj in inputstream:
        me = obj.data

        selection = [False] * len(me.vertices)
        me.vertices.foreach_set('select', selection)
        selection = [False] * len(me.edges)
        me.edges.foreach_set('select', selection)
        selection = [False] * len(me.polygons)
        me.polygons.foreach_set('select', selection)

        me.update()

    return (inputstream, None)


def select_by_expression(inputstream, options={}):
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
        if select_type == 'VERT':
            elements = bm.verts
        if select_type == 'EDGE':
            elements = bm.edges
        if select_type == 'FACE':
            elements = bm.faces

        try:
            values = evaluate_expression_foreach(elements, expression, obj, me, bm, select_type, default_ret=True)
            [elem.select_set(bool(value)) for elem, value in zip(elements, values)]
        except Exception as e:
            print('Failed to evaluate expression: ', str(e))

        # Finish up, write the bmesh back to the mesh
        bm.select_flush(False)
        bm.to_mesh(me)
        me.update()
        bm.free()

    return (inputstream, None)


def select_by_normal(inputstream, options={}):
    select_type = options['select_type']
    normal = options['normal']
    angle_tolerance = radians(options['angle_tolerance'])

    for obj in inputstream:
        me = obj.data

        # Get a BMesh representation
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        elements = []
        if select_type == 'VERT':
            elements = bm.verts
        if select_type == 'EDGE':
            elements = bm.verts
        if select_type == 'FACE':
            elements = bm.faces

        for elem in elements:
            angle = elem.normal.rotation_difference(normal).angle
            if angle < angle_tolerance:
                elem.select_set(True)

        # Finish up, write the bmesh back to the mesh
        bm.select_flush(False)
        bm.to_mesh(me)
        me.update()
        bm.free()

    return (inputstream, None)


def get_next_vert_wave(prev_vert_wave):
    next_vert_wave = []
    for vert in prev_vert_wave:
        for edge in vert.link_edges:
            other_vert = edge.other_vert(vert)
            if not other_vert.tag:
                setattr(other_vert, 'tag', True)
                next_vert_wave.append(other_vert)

    return next_vert_wave


def get_next_edge_wave(prev_edge_wave):
    next_edge_wave = []
    for edge in prev_edge_wave:
        for vert in edge.verts:
            for other_edge in vert.link_edges:
                if not other_edge.tag:
                    setattr(other_edge, 'tag', True)
                    next_edge_wave.append(other_edge)

    return next_edge_wave


def get_next_face_wave(prev_face_wave):
    next_face_wave = []
    for face in prev_face_wave:
        for edge in face.edges:
            for f in edge.link_faces:
                if not f.tag:
                    setattr(f, 'tag', True)
                    next_face_wave.append(f)

    return next_face_wave


def select_checkers(inputstream, options={}):
    select_type = options['select_type']
    select_flag = not options['select_flag']
    select_step = options['select_step']
    deselect_step = options['deselect_step']
    offset = options['offset']

    for obj in inputstream:
        me = obj.data

        # Get a BMesh representation
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        if len(bm.edges) == 0:
            continue

        select_toggle = select_flag
        next_step = select_step if select_toggle else deselect_step
        next_step = next_step - abs(offset) % (next_step + 1)

        if select_type == 'VERT':
            # first wave
            start_vert = bm.verts[0]
            start_vert.tag = True
            vert_wave = [start_vert]

            while len(vert_wave) > 0:
                for i in range(next_step):
                    for vert in vert_wave:
                        if select_toggle == select_flag:
                            setattr(vert, 'select', select_toggle)

                    vert_wave = get_next_vert_wave(vert_wave)

                select_toggle = not select_toggle
                next_step = select_step if select_toggle else deselect_step

        if select_type == 'EDGE':
            # first wave
            start_edge = bm.edges[0]
            start_edge.tag = True
            edge_wave = [start_edge]

            while len(edge_wave) > 0:
                for i in range(next_step):
                    for edge in edge_wave:
                        if select_toggle == select_flag:
                            setattr(edge, 'select', select_toggle)

                    edge_wave = get_next_edge_wave(edge_wave)

                select_toggle = not select_toggle
                next_step = select_step if select_toggle else deselect_step

        if select_type == 'FACE':
            if len(bm.faces) == 0:
                continue

            timer_start()

            # first wave
            start_face = bm.faces[0]
            start_face.tag = True
            face_wave = [start_face]

            while len(face_wave) > 0:
                for i in range(next_step):
                    for face in face_wave:
                        if select_toggle == select_flag:
                            setattr(face, 'select', select_toggle)

                    face_wave = get_next_face_wave(face_wave)

                select_toggle = not select_toggle
                next_step = select_step if select_toggle else deselect_step

            timer_end('checkers select: ')

        # Finish up, write the bmesh back to the mesh
        bm.select_flush(False)
        bm.to_mesh(me)
        me.update()
        bm.free()

    return (inputstream, None)
