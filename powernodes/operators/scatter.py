import bpy
import bmesh
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
from bpy_extras.mesh_utils import triangle_random_points

from .. ops import create_point_cloud
from .. utils.utils import timer_start, timer_end


def scatter_operator(inputstream, options={}):
    amount = options['amount']

    timer_start()

    objects = []
    for obj in inputstream:
        bhv_tree = BVHTree.FromObject(object=obj, depsgraph=bpy.context.evaluated_depsgraph_get(), epsilon=0.0)
        me = obj.data
        me.calc_loop_triangles()

        loop_triangles = [loop for loop in me.loop_triangles]

        coords = triangle_random_points(amount, loop_triangles)

        normals = [(0.0,0.0,0.0)] * len(coords)
        bvh_find_nearest = bhv_tree.find_nearest
        for index, co in enumerate(coords):
            (loc, norm, idx, dist) = bvh_find_nearest(co)
            normals[index] = norm if norm is not None else Vector((0,0,0))

        output_obj, _ = create_point_cloud(options={'coords': coords, 'edges': [], 'faces': []})

        for vert, normal in zip(output_obj.data.vertices, normals):
            vert.normal = normal

        objects.append(output_obj)

    timer_end('scatter: ')

    return (objects, None)
