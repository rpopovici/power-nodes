import bpy
import bmesh
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
import itertools

from .. utils.utils import timer_start, timer_end


def raycast_operator(inputstream0, inputstream1, options={}):
    distance = options['distance']
    project = options['project']
    use_intersect_normal = options['use_intersect_normal']

    timer_start()
    for target_obj in inputstream1:
        bhv_tree = BVHTree.FromObject(object=target_obj, depsgraph=bpy.context.evaluated_depsgraph_get(), epsilon=0.0)
        for select_obj in inputstream0:
            me = select_obj.data
            coords = [(0.0,0.0,0.0)] * len(me.vertices)

            bvh_ray_cast = bhv_tree.ray_cast
            for index, vert in enumerate(me.vertices):
                (loc, norm, idx, dist) = bvh_ray_cast(vert.co, -vert.normal, distance)
                coords[index] = loc if loc is not None else vert.co

            # result = [bhv_tree.ray_cast(vert.co, -vert.normal, distance) for vert in me.vertices]
            # coords = [location for (location, normal, index, distance) in result]
            # coords = [co if co else vert.co for co, vert in zip(coords, me.vertices)]

            coords = list(itertools.chain.from_iterable(coords))
            # coords = np.asarray(coords, dtype='f').ravel()

            me.vertices.foreach_set('co', coords)

    timer_end('raycast: ')

    return (inputstream0, None)
