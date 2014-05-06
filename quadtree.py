# quadtree.py
# Implements a Node and QuadTree class that can be used as 
# base classes for more sophisticated implementations.
# Malcolm Kesson Dec 19 2012

# edited Miklos Koren May 2, 2014

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

    def count_overlapping_points(self):
        return self.number_of_points

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
class QuadTree(object):
    maxdepth = 1 # the "depth" of the tree
    leaves = []
    allnodes = []
    #_______________________________________________________
    def __init__(self, rootnode, minrect):
        Node.minsize = minrect
        rootnode.subdivide() # constructs the network of nodes
        self.prune(rootnode)
        self.traverse(rootnode)
    #_______________________________________________________
    # Sets children of 'node' to None if they do not have any
    # LEAF nodes.        
    def prune(self, node):
        if node.type == Node.LEAF:
            return 1
        leafcount = 0
        removals = []
        for child in node.children:
            if child != None:
                leafcount += self.prune(child)
                if leafcount == 0:
                    removals.append(child)
        for item in removals:
            n = node.children.index(item)
            node.children[n] = None        
        return leafcount
    #_______________________________________________________
    # Appends all nodes to a "generic" list, but only LEAF 
    # nodes are appended to the list of leaves.
    def traverse(self, node):
        QuadTree.allnodes.append(node)
        if node.type == Node.LEAF:
            QuadTree.leaves.append(node)
            if node.depth > QuadTree.maxdepth:
                QuadTree.maxdepth = node.depth
        for child in node.children:
            if child != None:
                self.traverse(child) # << recursion