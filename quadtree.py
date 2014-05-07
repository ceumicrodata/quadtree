# quadtree.py
# Implements a Node and QuadTree class that can be used as 
# base classes for more sophisticated implementations.
# Malcolm Kesson Dec 19 2012

# edited Miklos Koren May 2, 2014
from shapely.geometry import Polygon as shapelyPolygon
from shapely.geometry import Point as shapelyPoint
from shapely.geometry.base import BaseGeometry

def point_in_rectangle(point, rectangle):
    x, z = point
    x0,z0,x1,z1 = rectangle
    return x >= x0 and x <= x1 and z >= z0 and z <= z1

class Feature(object):
    def __init__(self, geometry):
        if not isinstance(geometry, BaseGeometry):
            raise Exception
        self.geometry = geometry

    def contains_point(self, point):
        shPoint = shapelyPoint(point)
        return point_in_rectangle(point, self.geometry.bounds) and self.geometry.contains(shPoint)

    def contains_rectangle(self, rectangle):
        x0,z0,x1,z1 = rectangle
        points = [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]
        shPolygon = shapelyPolygon(points)
        return all([point_in_rectangle(point, self.geometry.bounds) for point in points]) and self.geometry.contains(shPolygon)

    def intersects_rectangle(self, rectangle):
        x0,z0,x1,z1 = rectangle
        points = [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]
        shPolygon = shapelyPolygon(points)
        return any([point_in_rectangle(point, self.geometry.bounds) for point in points]) and self.geometry.intersects(shPolygon)


class Node(object):
    ROOT = 0
    BRANCH = 1
    LEAF = 2
    #_______________________________________________________
    # In the case of a root node "parent" will be None. The
    # "rect" lists the minx,minz,maxx,maxz of the rectangle
    # represented by the node.
    def __init__(self, parent, rect, max_points=2):
        self.parent = parent
        self.children = []
        self.points = []
        self.number_of_points = 0
        self.max_points = max_points

        self.rectangle = tuple([float(item) for item in rect])
        self.type = Node.LEAF

    def add_point(self, point):
        if self.contains_point(point):
            if self.type==Node.LEAF:
                if len(self.points)+1 > self.max_points:
                    # the box is crowded, break it up in 4
                    self.subdivide()
                    # then try again
                    self.add_point(point)
                else:
                    self.points.append(point)
                    self.number_of_points += 1
            else:
                # find where the point goes
                for child in self.children:
                    if child.contains_point(point):
                        child.add_point(point)
                        self.number_of_points += 1
                        break 
        else:
            # point not in box, cannot place
            raise Exception

    def count_overlapping_points(self, feature):
        if feature.contains_rectangle(self.rectangle):
            # all points are within
            return self.number_of_points
        elif feature.intersects_rectangle(self.rectangle):
            if self.type==Node.LEAF:
                # we cannot continue recursion, do a "manual" count
                return sum([1 for point in self.points if feature.contains_point(point)])
            else:
                return sum([child.count_overlapping_points(feature) for child in self.children])
        else:
            return 0

    #_______________________________________________________
    # Recursively subdivides a rectangle. Division occurs 
    # ONLY if the rectangle spans a "feature of interest".
    def subdivide(self):
        if not self.type == Node.LEAF:
            # only leafs can be subdivided
            raise Exception
        points = self.points
        self.points = []
        self.type = Node.BRANCH
    
        x0,z0,x1,z1 = self.rectangle
        half_width = (x1 - x0)/2
        half_height = (z1 - z0)/2
        rects = []
        rects.append( (x0, z0, x0 + half_width, z0 + half_height) )
        rects.append( (x0, z0 + half_height, x0 + half_width, z1) )
        rects.append( (x0 + half_width, z0 + half_height, x1, z1) )
        rects.append( (x0 + half_width, z0, x1, z0 + half_height) )
        for rect in rects:
            self.children.append(Node(self, rect, self.max_points))
        for point in points:
            for child in self.children:
                if child.contains_point(point):
                    child.add_point(point)
                    break


    #_______________________________________________________
    # A utility proc that returns True if the coordinates of
    # a point are within the bounding box of the node.
    def contains_point(self, point):
        x, z = point
        x0,z0,x1,z1 = self.rectangle
        if x >= x0 and x <= x1 and z >= z0 and z <= z1:
            return True
        else:
            return False
  
#===========================================================            
class QuadTree(Node):
    #_______________________________________________________
    def __init__(self, points):
        minx = min([point[0] for point in points])
        minz = min([point[1] for point in points])
        maxx = max([point[0] for point in points])
        maxz = max([point[1] for point in points])
        # if a split involves 16 checks of containment, the optimal number of points is 16/ln(4)
        super(QuadTree, self).__init__(None, rect=(minx,minz,maxx,maxz), max_points=11)
        for point in points:
            self.add_point(point)
