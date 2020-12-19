import bpy
import bmesh
from mathutils import Vector, Matrix
from mathutils.noise import noise_vector, hetero_terrain, hybrid_multi_fractal, random_vector, seed_set
import numpy as np

from .. utils.utils import timer_start, timer_end


def random_operator(inputstream, options={}):
    select_type = options['select_type']
    seed = options['seed']
    factor = options['factor']

    for index, obj in enumerate(inputstream):
        if select_type == 'OBJECT':
            obj.location += factor * random_vector()
        elif select_type == 'VERT':
            me = obj.data

            # Get a BMesh representation
            bm = bmesh.new()
            bm.from_mesh(me)
            bm.verts.ensure_lookup_table()

            timer_start()

            seed_set(seed + index)
            for v in bm.verts: v.co = v.co + factor * random_vector()

            timer_end('random: ')

            # Finish up, write the bmesh back to the mesh
            bm.to_mesh(me)
            me.update()
            bm.free()

    return (inputstream, None)


def noise_operator(inputstream, options={}):
    factor = options['factor']

    for obj in inputstream:  

        me = obj.data

        # Get a BMesh representation
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.verts.ensure_lookup_table()

        for v in bm.verts: v.co = v.co + factor * noise_vector(v.co)

        # Finish up, write the bmesh back to the mesh
        bm.to_mesh(me)
        me.update()
        bm.free()

    return (inputstream, None)


def terrain_noise_operator(inputstream, options={}):
    factor = options['factor']
    H = options['H']
    lacunarity = options['lacunarity']
    octaves = options['octaves']
    offset = options['offset']
    noise_basis = options['noise_basis']
    
    for obj in inputstream:
        me = obj.data

        # Get a BMesh representation
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.verts.ensure_lookup_table()

        terrain = [hetero_terrain(v.co, H, lacunarity, octaves, offset, noise_basis=noise_basis) for v in bm.verts]

        for v, t in zip(bm.verts, terrain): v.co = v.co + factor * t * v.normal

        # Finish up, write the bmesh back to the mesh
        bm.to_mesh(me)
        me.update()
        bm.free()

    return (inputstream, None)


def hybrid_multi_fractal_noise_operator(inputstream, options={}):
    factor = options['factor']
    H = options['H']
    lacunarity = options['lacunarity']
    octaves = options['octaves']
    offset = options['offset']
    gain = options['gain']
    noise_basis = options['noise_basis']

    for obj in inputstream:
        mesh = obj.data

        vertices = np.empty((len(mesh.vertices), 3), 'f')
        normals = np.empty((len(mesh.vertices), 3), 'f')
        # hmf_noise = np.zeros(len(mesh.vertices), 'f')

        mesh.vertices.foreach_get(
            "co", np.reshape(vertices, len(mesh.vertices) * 3))

        mesh.vertices.foreach_get(
            "normal", np.reshape(normals, len(mesh.vertices) * 3))

        hmf_noise = np.asarray([hybrid_multi_fractal(co, H, lacunarity, octaves, offset, gain, noise_basis=noise_basis) for co in vertices])

        vertices += normals * hmf_noise[:, np.newaxis] * factor

        mesh.vertices.foreach_set('co', vertices.ravel())

        mesh.update()

    return (inputstream, None)
