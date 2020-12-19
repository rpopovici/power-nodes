import math
import operator
from . geom import Polygon, BSPNode, Vertex, Vector, PolygonType, PolygonListType, VectorType, VertexType, BSPNodeType
from functools import reduce

import numba as nb
from numba import jit, njit, objmode, generated_jit, types, typed
from numba.experimental import jitclass
from numba import int64, float32, float64

from ..... utils.utils import timer_start, timer_end


@jitclass([('polygons', PolygonListType) ])  
class CSG(object):
    """
    Constructive Solid Geometry (CSG) is a modeling technique that uses Boolean
    operations like union and intersection to combine 3D solids. This library
    implements CSG operations on meshes elegantly and concisely using BSP trees,
    and is meant to serve as an easily understandable implementation of the
    algorithm. All edge cases involving overlapping coplanar polygons in both
    solids are correctly handled.
    
    Example usage::
    
        from csg.core import CSG
        
        cube = CSG.cube();
        sphere = CSG.sphere({'radius': 1.3});
        polygons = cube.subtract(sphere).toPolygons();
    
    ## Implementation Details
    
    All CSG operations are implemented in terms of two functions, `clipTo()` and
    `invert()`, which remove parts of a BSP tree inside another BSP tree and swap
    solid and empty space, respectively. To find the union of `a` and `b`, we
    want to remove everything in `a` inside `b` and everything in `b` inside `a`,
    then combine polygons from `a` and `b` into one solid::
    
        a.clipTo(b);
        b.clipTo(a);
        a.build(b.allPolygons());
    
    The only tricky part is handling overlapping coplanar polygons in both trees.
    The code above keeps both copies, but we need to keep them in one tree and
    remove them in the other tree. To remove them from `b` we can clip the
    inverse of `b` against `a`. The code for union now looks like this::
    
        a.clipTo(b);
        b.clipTo(a);
        b.invert();
        b.clipTo(a);
        b.invert();
        a.build(b.allPolygons());
    
    Subtraction and intersection naturally follow from set operations. If
    union is `A | B`, subtraction is `A - B = ~(~A | B)` and intersection is
    `A & B = ~(~A | ~B)` where `~` is the complement operator.
    
    ## License
    
    Copyright (c) 2011 Evan Wallace (http://madebyevan.com/), under the MIT license.
    
    Python port Copyright (c) 2012 Tim Knip (http://www.floorplanner.com), under the MIT license.
    Additions by Alex Pletzer (Pennsylvania State University)
    """
    def __init__(self, polygons):
        self.polygons = polygons


    def clone(self):
        polygons = typed.List.empty_list(PolygonType) #[p.clone() for p in self.polygons] #list(map(lambda p: p.clone(), self.polygons))
        for p in self.polygons:
            polygons.append(p.clone())
        return CSG(polygons)


    def toPolygons(self, result):
        for p in self.polygons:
            result.append(p)
        # return self.polygons


    def union(self, csg):
        """
        Return a new CSG solid representing space in either this solid or in the
        solid `csg`. Neither this solid nor the solid `csg` are modified.::
        
            A.union(B)
        
            +-------+            +-------+
            |       |            |       |
            |   A   |            |       |
            |    +--+----+   =   |       +----+
            +----+--+    |       +----+       |
                 |   B   |            |       |
                 |       |            |       |
                 +-------+            +-------+
        """
        a = BSPNode(self.polygons)
        b = BSPNode(csg.polygons)
        a.clipTo(b)
        b.clipTo(a)
        b.invert()
        b.clipTo(a)
        b.invert()
        b_all_polys = typed.List.empty_list(PolygonType)
        b.allPolygons(b_all_polys)
        a.build(b_all_polys)
        a_all_polys = typed.List.empty_list(PolygonType)
        a.allPolygons(a_all_polys)
        return CSG(a_all_polys)

        
    def subtract(self, csg):
        """
        Return a new CSG solid representing space in this solid but not in the
        solid `csg`. Neither this solid nor the solid `csg` are modified.::
        
            A.subtract(B)
        
            +-------+            +-------+
            |       |            |       |
            |   A   |            |       |
            |    +--+----+   =   |    +--+
            +----+--+    |       +----+
                 |   B   |
                 |       |
                 +-------+
        """
        a = BSPNode(self.polygons)
        b = BSPNode(csg.polygons)
        a.invert()
        a.clipTo(b)
        b.clipTo(a)
        b.invert()
        b.clipTo(a)
        b.invert()
        b_all_polys = typed.List.empty_list(PolygonType)
        b.allPolygons(b_all_polys)
        a.build(b_all_polys)
        a.invert()
        a_all_polys = typed.List.empty_list(PolygonType)
        a.allPolygons(a_all_polys)
        return CSG(a_all_polys)

        
    def intersect(self, csg):
        """
        Return a new CSG solid representing space both this solid and in the
        solid `csg`. Neither this solid nor the solid `csg` are modified.::
        
            A.intersect(B)
        
            +-------+
            |       |
            |   A   |
            |    +--+----+   =   +--+
            +----+--+    |       +--+
                 |   B   |
                 |       |
                 +-------+
        """
        a = BSPNode(self.polygons)
        b = BSPNode(csg.polygons)
        a.invert()
        b.clipTo(a)
        b.invert()
        a.clipTo(b)
        b.clipTo(a)
        b_all_polys = typed.List.empty_list(PolygonType)
        b.allPolygons(b_all_polys)        
        a.build(b_all_polys)
        a.invert()
        a_all_polys = typed.List.empty_list(PolygonType)
        a.allPolygons(a_all_polys)        
        return CSG(a_all_polys)


CSGType = CSG.class_type.instance_type


MeshType = nb.types.ListType(nb.types.ListType(nb.types.ListType(float64)))

@njit((MeshType, MeshType, types.string), cache=True, nogil=True, parallel=False, fastmath=False, boundscheck=False, inline='always')
def bool_csg_mesh_native(mesh_data_target, mesh_data_cutter, operation_type):
    polygons_a = typed.List.empty_list(PolygonType)
    polygons_b = typed.List.empty_list(PolygonType)

    for polygon in mesh_data_target:
        vertices = typed.List.empty_list(VertexType)
        for v in polygon:
             vertices.append( Vertex(Vector(v[0], v[1], v[2]), Vector(0,0,0)) )
        polygons_a.append( Polygon(vertices, int64(polygon[0][3] )) )

    for polygon in mesh_data_cutter:
        vertices = typed.List.empty_list(VertexType)
        for v in polygon:
             vertices.append( Vertex(Vector(v[0], v[1], v[2]), Vector(0,0,0)) )
        polygons_b.append( Polygon(vertices, int64( polygon[0][3] )) )

    a = CSG(polygons_a)
    b = CSG(polygons_b)

    output_polygons = typed.List.empty_list(PolygonType)
    if operation_type == 'DIFFERENCE':
        a.subtract(b).toPolygons(output_polygons)
    elif operation_type == 'UNION':
        a.union(b).toPolygons(output_polygons)
    elif operation_type == 'INTERSECT':
        a.intersect(b).toPolygons(output_polygons)

    polygons = [] # typed.List()
    for polygon in output_polygons:
        vertices = [] # typed.List()
        for vert in polygon.vertices:
            vlist = [] # typed.List()
            vlist.append(vert.pos.x)
            vlist.append(vert.pos.y)
            vlist.append(vert.pos.z)
            vlist.append(float64(polygon.shared))
            vertices.append(vlist)
        polygons.append(vertices)
    
    return polygons


def bool_csg_mesh(mesh_data_target, mesh_data_cutter, operation_type):
    polygons_a = typed.List.empty_list(nb.types.ListType(nb.types.ListType(float64)))
    for polygon in mesh_data_target:
        vertices = typed.List.empty_list(nb.types.ListType(float64))
        for v in polygon['vertices']:
            vertex = typed.List.empty_list(float64)
            for val in v:
                vertex.append(float(val))
            vertex.append(float(polygon['shared']))
            vertices.append(vertex)
        polygons_a.append(vertices)

    polygons_b = typed.List.empty_list(nb.types.ListType(nb.types.ListType(float64)))
    for polygon in mesh_data_cutter:
        vertices = typed.List.empty_list(nb.types.ListType(float64))
        for v in polygon['vertices']:
            vertex = typed.List.empty_list(float64)
            for val in v:
                vertex.append(float(val))
            vertex.append(float(polygon['shared']))
            vertices.append(vertex)
        polygons_b.append(vertices)

    timer_start()
    res = bool_csg_mesh_native(polygons_a, polygons_b, operation_type)
    timer_end('njit ')
    return res


# needed because jitclass is not cacheable
import threading
def background_task():
    dummy_mesh_a = [{'selected': 1, 'shared': 0, 'vertices': [(1.0, 1.0, 1.0), (-1.0, 1.0, 1.0), (-1.0, -1.0, 1.0), (1.0, -1.0, 1.0)]}]
    dummy_mesh_a = [{'selected': 1, 'shared': 0, 'vertices': [(1.0, 1.0, 1.0), (-1.0, 1.0, 1.0), (-1.0, -1.0, 1.0), (1.0, -1.0, 1.0)]}]
    bool_csg_mesh(dummy_mesh_a, dummy_mesh_a, 'UNION')

def execute_in_background():
    background_thread = threading.Thread(target=background_task, name="Background Task")
    background_thread.start()

execute_in_background()
