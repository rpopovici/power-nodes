import math
import sys
from functools import reduce

import numba as nb
from numba import int32, int64, float32, float64, optional
from numba import jit, njit, types, typed, prange
from numba.experimental import jitclass
from numba.extending import overload_method, overload


@jitclass([('x', float64), ('y', float64), ('z', float64)])
class Vector(object):
    """
    class Vector

    Represents a 3D vector.
    
    Example usage:
         Vector(1, 2, 3);
         Vector([1, 2, 3]);
         Vector({ 'x': 1, 'y': 2, 'z': 3 });
    """
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    # def __repr__(self):
    #     return '({0}, {1}, {2})'.format(self.x, self.y, self.z)
            
    def clone(self):
        """ Clone. """
        return self #Vector(self.x, self.y, self.z)
        
    def negated(self):
        """ Negated. """
        return Vector(-self.x, -self.y, -self.z)

    # def __neg__(self):
    #     return self.negated()
    
    def plus(self, a):
        """ Add. """
        return Vector(self.x+a.x, self.y+a.y, self.z+a.z)

    # def __add__(self, a):
    #     return self.plus(a)
    
    def minus(self, a):
        """ Subtract. """
        return Vector(self.x-a.x, self.y-a.y, self.z-a.z)

    # def __sub__(self, a):
    #     return self.minus(a)
    
    def times(self, a):
        """ Multiply. """
        return Vector(self.x*a, self.y*a, self.z*a)

    # def __mul__(self, a):
    #     return self.times(a)
            
    def dividedBy(self, a):
        """ Divide. """
        if a == 0.0:
            return Vector(0.0, 0.0, 0.0)
        else:
            return Vector(self.x/a, self.y/a, self.z/a)

    # def __truediv__(self, a):
    #     return self.dividedBy(float(a))

    # def __div__(self, a):
    #     return self.dividedBy(float(a))
    
    def dot(self, a):
        """ Dot. """
        return self.x*a.x + self.y*a.y + self.z*a.z
    
    def lerp(self, a, t):
        """ Lerp. Linear interpolation from self to a"""
        return self.plus(a.minus(self).times(t))
    
    def length(self):
        """ Length. """
        return math.sqrt(self.dot(self))
    
    def unit(self):
        """ Normalize. """
        return self.dividedBy(self.length())
        
    def cross(self, a):
        """ Cross. """
        return Vector(
            self.y * a.z - self.z * a.y,
            self.z * a.x - self.x * a.z,
            self.x * a.y - self.y * a.x)
          
    # def __getitem__(self, key):
    #     if key == 'x':
    #         return self.x
    #     if key == 'y':
    #         return self.y
    #     if key == 'z':
    #         return self.z                        
    #     #return (self.x, self.y, self.z)[key]

    # def __setitem__(self, key, value):
    #     if key == 'x':
    #         self.x = value
    #     if key == 'y':
    #         self.y = value
    #     if key == 'z':
    #         self.z = value           
        # l = [self.x, self.y, self.z]
        # l[key] = value
        # self.x, self.y, self.z = l
            
    # def __len__(self):
    #     return 3
    
    # def __iter__(self):
    #     return iter((self.x, self.y, self.z))
            
    # def __repr__(self):
    #     return 'Vector(%.2f, %.2f, %0.2f)' % (self.x, self.y, self.z) 


VectorType = Vector.class_type.instance_type

@jitclass([('pos', VectorType), ('normal', VectorType)])     
class Vertex(object):
    """ 
    Class Vertex 

    Represents a vertex of a polygon. Use your own vertex class instead of this
    one to provide additional features like texture coordinates and vertex
    colors. Custom vertex classes need to provide a `pos` property and `clone()`,
    `flip()`, and `interpolate()` methods that behave analogous to the ones
    defined by `Vertex`. This class provides `normal` so convenience
    functions like `CSG.sphere()` can return a smooth vertex normal, but `normal`
    is not used anywhere else.
    """
    def __init__(self, pos, normal):
        self.pos = Vector(pos.x, pos.y, pos.z)
        self.normal = Vector(normal.x, normal.y, normal.z)


    def clone(self):
        return self #Vertex(self.pos.clone(), self.normal.clone())
    
    def flip(self):
        """
        Invert all orientation-specific data (e.g. vertex normal). Called when the
        orientation of a polygon is flipped.
        """
        self.normal = self.normal.negated()

    def interpolate(self, other, t):
        """
        Create a new vertex between this vertex and `other` by linearly
        interpolating all properties using a parameter of `t`. Subclasses should
        override this to interpolate additional properties.
        """
        return Vertex(self.pos.lerp(other.pos, t), 
                          self.normal.lerp(other.normal, t))

    # def __repr__(self):
    #     return repr(self.pos)

VertexType = Vertex.class_type.instance_type


EPSILON = 1.e-5

COPLANAR = 0 # all the vertices are within EPSILON distance from plane
FRONT = 1 # all the vertices are in front of the plane
BACK = 2 # all the vertices are at the back of the plane
SPANNING = 3 # some vertices are in front, some in the back


@jitclass([('normal', VectorType), ('w', float64)])                             
class Plane(object):
    """
    class Plane

    Represents a plane in 3D space.
    """
    
    """
    `Plane.EPSILON` is the tolerance used by `splitPolygon()` to decide if a
    point is on the plane.
    """

    def __init__(self, normal, w):
        self.normal = normal
        # w is the (perpendicular) distance of the plane from (0, 0, 0)
        self.w = w
    

    def clone(self):
        return Plane(self.normal.clone(), self.w)
        
    def flip(self):
        self.normal = self.normal.negated()
        self.w = -self.w

    # def __repr__(self):
    #     return 'normal: {0} w: {1}'.format(self.normal, self.w)
    
    def splitPolygon(self, polygon, coplanarFront, coplanarBack, front, back):
        """
        Split `polygon` by this plane if needed, then put the polygon or polygon
        fragments in the appropriate lists. Coplanar polygons go into either
        `coplanarFront` or `coplanarBack` depending on their orientation with
        respect to this plane. Polygons in front or in back of this plane go into
        either `front` or `back`
        """
        # COPLANAR = 0 # all the vertices are within EPSILON distance from plane
        # FRONT = 1 # all the vertices are in front of the plane
        # BACK = 2 # all the vertices are at the back of the plane
        # SPANNING = 3 # some vertices are in front, some in the back

        # Classify each point as well as the entire polygon into one of the above
        # four classes.
        polygonType = 0
        vertexLocs = typed.List.empty_list(int64)
        
        numVertices = len(polygon.vertices)
        for i in range(numVertices):
            t = self.normal.dot(polygon.vertices[i].pos) - self.w
            loc = -1
            if t < -EPSILON: 
                loc = BACK
            elif t > EPSILON: 
                loc = FRONT
            else: 
                loc = COPLANAR
            polygonType |= loc
            vertexLocs.append(loc)
    
        # Put the polygon in the correct list, splitting it when necessary.
        if polygonType == COPLANAR:
            normalDotPlaneNormal = self.normal.dot(polygon.plane.normal)
            if normalDotPlaneNormal > 0:
                coplanarFront.append(polygon)
            else:
                coplanarBack.append(polygon)
        elif polygonType == FRONT:
            front.append(polygon)
        elif polygonType == BACK:
            back.append(polygon)
        elif polygonType == SPANNING:
            f = typed.List.empty_list(VertexType)
            b = typed.List.empty_list(VertexType)
            for i in range(numVertices):
                j = (i+1) % numVertices
                ti = vertexLocs[i]
                tj = vertexLocs[j]
                vi = polygon.vertices[i]
                vj = polygon.vertices[j]
                if ti != BACK: 
                    f.append(vi)
                if ti != FRONT:
                    if ti != BACK: 
                        b.append(vi.clone())
                    else:
                        b.append(vi)
                if (ti | tj) == SPANNING:
                    # interpolation weight at the intersection point
                    t = (self.w - self.normal.dot(vi.pos)) / self.normal.dot(vj.pos.minus(vi.pos))
                    # intersection point on the plane
                    v = vi.interpolate(vj, t)
                    f.append(v)
                    b.append(v.clone())
            if len(f) >= 3: 
                front.append(Polygon(f, polygon.shared))
            if len(b) >= 3: 
                back.append(Polygon(b, polygon.shared))

PlaneType = Plane.class_type.instance_type


VertexListType = types.ListType(VertexType)

@jitclass([('vertices', VertexListType), ('shared', int64), ('plane', PlaneType)])  
class Polygon(object):
    """
    class Polygon

    Represents a convex polygon. The vertices used to initialize a polygon must
    be coplanar and form a convex loop. They do not have to be `Vertex`
    instances but they must behave similarly (duck typing can be used for
    customization).
    
    Each convex polygon has a `shared` property, which is shared between all
    polygons that are clones of each other or were split from the same polygon.
    This can be used to define per-polygon properties (such as surface color).
    """
    def __init__(self, vertices, shared):
        self.vertices = vertices
        self.shared = shared

        # determine polygon plane
        a = vertices[0].pos
        b = vertices[1].pos
        c = vertices[2].pos
        n = b.minus(a).cross(c.minus(a)).unit()
        self.plane = Plane(n, n.dot(a))        
        # self.plane = PlanefromPoints(vertices[0].pos, vertices[1].pos, vertices[2].pos)
    
    def clone(self):
        return self
        # vertices = typed.List.empty_list(VertexType) #[v.clone() for v in self.vertices] #list(map(lambda v: v.clone(), self.vertices))
        # for v in self.vertices:
        #     vertices.append(v.clone())
        # return Polygon(vertices, self.shared)
                
    def flip(self):
        self.vertices.reverse()
        #map(lambda v: v.flip(), self.vertices)
        for v in self.vertices:
            v.flip()
        self.plane.flip()

    # def __repr__(self):
    #     return reduce(lambda x,y: x+y,
    #                   ['Polygon(['] + [repr(v) + ', ' \
    #                                    for v in self.vertices] + ['])'], '')

PolygonType = Polygon.class_type.instance_type


PolygonListType = types.ListType(PolygonType)
BSPNodeType = nb.deferred_type()


@jitclass([('plane', nb.optional(PlaneType)), ('front', nb.optional(BSPNodeType)), ('back', nb.optional(BSPNodeType)), ('polygons', nb.optional(PolygonListType)) ]) 
class BSPNode(object):
    """
    class BSPNode

    Holds a node in a BSP tree. A BSP tree is built from a collection of polygons
    by picking a polygon to split along. That polygon (and all other coplanar
    polygons) are added directly to that node and the other polygons are added to
    the front and/or back subtrees. This is not a leafy BSP tree since there is
    no distinction between internal and leaf nodes.
    """
    def __init__(self, polygons):
        self.plane = None # Plane instance
        self.front = None # BSPNode
        self.back = None  # BSPNode
        self.polygons = typed.List.empty_list(PolygonType)
        if polygons is not None:
            self.build(polygons)
            
    def clone(self):
        ret = BSPNode(None)
        nodes = typed.List()
        nodes.append((self, ret))
        while len(nodes):
            original, clone = nodes.pop(0)

            clone.polygons = typed.List.empty_list(PolygonType)
            for p in original.polygons:
                clone.polygons.append(p.clone())
        
            clone.plane = original.plane.clone()

            if original.front is not None:
                clone.front = BSPNode(None)
                nodes.append((original.front, clone.front))
            if original.back is not None:
                clone.back = BSPNode(None)
                nodes.append((original.back, clone.back))

        return ret
        
    def invert(self):
        """ 
        Convert solid space to empty space and empty space to solid space.
        """
        nodes = typed.List()
        nodes.append(self)
        while len(nodes):
            node = nodes.pop(0)

            for poly in node.polygons:
                poly.flip()
            node.plane.flip()

            #swap
            temp = node.front
            node.front = node.back
            node.back = temp

            if node.front is not None: 
                nodes.append(node.front)
            if node.back is not None: 
                nodes.append(node.back)
        

    def clipPolygons(self, polygons, result):
        """ 
        Recursively remove all polygons in `polygons` that are inside this BSP
        tree.
        """
        # result = typed.List.empty_list(PolygonType)
        clips = typed.List()
        clips.append((self, polygons))
        while len(clips):
            node, polygons  = clips.pop(0)

            if node.plane is None:
                for p in polygons:
                    result.append(p)
                # result.extend(polygons)
                continue

            front = typed.List.empty_list(PolygonType)
            back = typed.List.empty_list(PolygonType)
            for poly in polygons:
                node.plane.splitPolygon(poly, front, back, front, back)

            if node.front is not None: 
                clips.append((node.front, front))
            else:
                for p in front:
                    result.append(p)                
                # result.extend(front)

            if node.back is not None: 
                clips.append((node.back, back))

        # return result
        
    def clipTo(self, other):
        """ 
        Remove all polygons in this BSP tree that are inside the other BSP tree
        `other`.
        """
        nodes = typed.List.empty_list(BSPNodeType)
        nodes.append(self)
        while len(nodes):
            node = nodes.pop(0)

            if node.polygons is not None:
                result = typed.List.empty_list(PolygonType)
                other.clipPolygons(node.polygons, result)
                node.polygons.clear()
                for p in result:
                    node.polygons.append(p)
            if node.front is not None: 
                nodes.append(node.front)
            if node.back is not None: 
                nodes.append(node.back)
        

    def allPolygons(self, result):
        """
        Return a list of all polygons in this BSP tree.
        """
        # result = typed.List()
        nodes = typed.List()
        nodes.append(self)
        while len(nodes):
            node = nodes.pop(0)
                    
            for p in node.polygons:
                result.append(p)                    
            # result.extend(node.polygons)
            if node.front is not None: 
                nodes.append(node.front)
            if node.back is not None: 
                nodes.append(node.back)

        # return result
        
    def build(self, polygons):
        """
        Build a BSP tree out of `polygons`. When called on an existing tree, the
        new polygons are filtered down to the bottom of the tree and become new
        nodes there. Each set of polygons is partitioned using the first polygon
        (no heuristic is used to pick a good split).
        """
        if len(polygons) == 0:
            return

        builds = typed.List()
        builds.append((self, polygons))
        while len(builds):
            node, polygons = builds.pop(0)

            cut = int64(len(polygons) / 2)

            if node.plane is None: 
                node.plane = polygons[cut].plane.clone()
            # add polygon to this node
            node.polygons.append(polygons[cut])
            front = typed.List.empty_list(PolygonType)
            back = typed.List.empty_list(PolygonType)
            # split all other polygons using the first polygon's plane
            for idx in range(len(polygons)):
                # coplanar front and back polygons go into self.polygons
                poly = polygons[idx]
                if idx != cut:
                    node.plane.splitPolygon(poly, node.polygons, node.polygons,
                                        front, back)
            # recursively build the BSP tree
            if len(front) > 0:
                if node.front is None:
                    node.front = BSPNode(None)
                # self.front.build(front)
                builds.append((node.front, front))
            if len(back) > 0:
                if node.back is None:
                    node.back = BSPNode(None)
                # self.back.build(back)
                builds.append((node.back, back))


BSPNodeType.define(BSPNode.class_type.instance_type)
