# quadtree.py
# Implements a Node and QuadTree class that can be used as 
# base classes for more sophisticated implementations.
# Malcolm Kesson Dec 19 2012

# edited Miklos Koren May 2, 2014
from shapely.geometry import Polygon as shapelyPolygon
from shapely.geometry import Point as shapelyPoint
from shapely.geometry.base import BaseGeometry

def featurize(point):
    try:
        if point['type']=='Feature' and 'geometry' in point and 'properties' in point:
            return point
        else:
            raise Exception
    except:
        try:
            if point['type']=='Point' and 'coordinates' in point:
                return geometry_to_feature(point)
            else:
                raise Exception
        except:
            return point_to_feature(point)

def geometry_to_point(geometry):
    return tuple(geometry['coordinates'])

def feature_to_point(feature):
    return geometry_to_point(feature['geometry'])

def point_to_feature(point):
    return {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": list(point)
      },
      "properties": {
        "name": "Dinagat Islands"
      }
    }

def geometry_to_feature(geometry):
    return {
      "type": "Feature",
      "geometry": geometry,
      "properties": {
      }
    }

def point_in_rectangle(point, rectangle):
    x, z = point
    x0,z0,x1,z1 = rectangle
    return x >= x0 and x <= x1 and z >= z0 and z <= z1

class Feature(object):
    '''
    A wrapper around shapely geometries.
    '''
    def __init__(self, geometry):
        if not isinstance(geometry, BaseGeometry):
            raise Exception
        self.geometry = geometry

    def contains_point(self, point):
        if self.geometry.is_empty:
            return False
        pure_point = feature_to_point(featurize(point))
        shPoint = shapelyPoint(pure_point)
        return point_in_rectangle(pure_point, self.geometry.bounds) and self.geometry.contains(shPoint)

    def contains_rectangle(self, rectangle):
        if self.geometry.is_empty:
            return False
        x0,z0,x1,z1 = rectangle
        points = [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]
        shPolygon = shapelyPolygon(points)
        return all([point_in_rectangle(point, self.geometry.bounds) for point in points]) and self.geometry.contains(shPolygon)

    def intersects_rectangle(self, rectangle):
        if self.geometry.is_empty:
            return False
        x0,z0,x1,z1 = rectangle
        points = [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]
        shPolygon = shapelyPolygon(points)
        return not self.geometry.disjoint(shPolygon)


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
        self._points = {}
        self.features = []
        self.number_of_points = 0
        self.max_points = max_points

        self.rectangle = tuple([float(item) for item in rect])
        self.type = Node.LEAF

    @property
    def points(self):
        points = []
        for coordinate, frequency in self._points.items():
            points.extend([coordinate]*frequency)
        return points

    def add_point(self, point):
        point_feature = featurize(point)
        point = feature_to_point(point_feature)
        if self.contains_point(point_feature):
            if self.type==Node.LEAF:
                if point in self._points:
                    self._points[point] += 1
                else:
                    self._points[point] = 1
                self.features.append(point_feature)
                self.number_of_points += 1
                if len(self._points) > self.max_points:
                    # the box is crowded, break it up in 4
                    self.subdivide()
            else:
                # find where the point goes
                for child in self.children:
                    if child.contains_point(point_feature):
                        child.add_point(point_feature)
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
                return sum([frequency for point, frequency in self._points.items() if feature.contains_point(point)])
            else:
                return sum([child.count_overlapping_points(feature) for child in self.children])
        else:
            return 0

    def get_overlapping_points(self, feature):
        if feature.contains_rectangle(self.rectangle):
            # all points are within
            return self.get_all_points()
        elif feature.intersects_rectangle(self.rectangle):
            if self.type==Node.LEAF:
                # we cannot continue recursion, do a "manual" count
                return [point for point in self.features if feature.contains_point(point)]
            else:
                output = []
                for child in self.children:
                    output.extend(child.get_overlapping_points(feature))
                return output
        else:
            return []

    def get_all_points(self):
        if self.type == Node.LEAF:
            return self.features
        else:
            output = []
            for child in self.children:
                output.extend(child.get_all_points())
            return output

    #_______________________________________________________
    # Recursively subdivides a rectangle. Division occurs 
    # ONLY if the rectangle spans a "feature of interest".
    def subdivide(self):
        if not self.type == Node.LEAF:
            # only leafs can be subdivided
            raise Exception
        features = self.features
        self._points = {}
        self.features = []
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
        for point in features:
            for child in self.children:
                if child.contains_point(point):
                    child.add_point(point)
                    break


    #_______________________________________________________
    # A utility proc that returns True if the coordinates of
    # a point are within the bounding box of the node.
    def contains_point(self, point):
        point = feature_to_point(featurize(point))
        x, z = point
        x0,z0,x1,z1 = self.rectangle
        if x >= x0 and x <= x1 and z >= z0 and z <= z1:
            return True
        else:
            return False

    def walk(self):
        ''' An iterator over the points of in the Node'''
        if self.type==Node.LEAF:
            for point in self.points:
                yield point
        else:
            for child in self.children:
                for point in child.walk():
                    yield point

  
#===========================================================            
class QuadTree(Node):
    #_______________________________________________________
    def __init__(self, points):
        pure_points = [feature_to_point(featurize(point)) for point in points]
        minx = min([point[0] for point in pure_points])
        minz = min([point[1] for point in pure_points])
        maxx = max([point[0] for point in pure_points])
        maxz = max([point[1] for point in pure_points])
        # if a split involves 16 checks of containment, the optimal number of points is 16/ln(4)
        super(QuadTree, self).__init__(None, rect=(minx,minz,maxx,maxz), max_points=11)
        for point in points:
            self.add_point(point)
