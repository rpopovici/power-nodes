import bpy
import bmesh
from functools import reduce

from .. ops import delete_interior_faces, fix_t_junction


def delete_loose(obj, options={'verts': True, 'edges': False, 'faces': False}):
    me = obj.data
    # Get a BMesh representation
    bm = bmesh.new()
    bm.from_mesh(me)

    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    if options['faces']:
        # faces with no linked faces
        # select faces if all edges are boundary
        faces = [f for f in bm.faces if reduce(lambda acc, e: acc and e.is_boundary, f.edges, True)]
        bmesh.ops.delete(bm, geom=faces, context='FACES')

    if options['edges']:
        # edges with no linked faces
        edges = [e for e in bm.edges if not e.link_faces]
        bmesh.ops.delete(bm, geom=edges, context='EDGES')

    if options['verts']:
        # verts with no linked faces
        verts = [v for v in bm.verts if not v.link_edges]
        bmesh.ops.delete(bm, geom=verts, context='VERTS')

    # Finish up, write the bmesh back to the mesh
    bm.to_mesh(me)
    me.update()
    bm.free()


def clean_operator(inputstream, options={}):
    delete_interior = options['delete_interior']
    delete_loose_verts = options['delete_loose_verts']
    delete_loose_edges = options['delete_loose_edges']
    delete_loose_faces = options['delete_loose_faces']
    fix_tjunction = options['fix_t_junction']

    for obj in inputstream:
        if delete_interior:
            delete_interior_faces(obj)

        if delete_loose_verts or delete_loose_edges or delete_loose_faces:
            delete_loose(obj, options = {'verts': delete_loose_verts, 'edges': delete_loose_edges, 'faces': delete_loose_faces})

        if fix_tjunction:
            fix_t_junction(obj)

    return (inputstream, None)
