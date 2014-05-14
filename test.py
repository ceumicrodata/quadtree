import quadtree as module
import unittest as ut
from shapely.geometry import Polygon
from shapely.geometry import asShape
import json

class Feature(module.Node):
    def contains_rectangle(self, rectangle):
        # untested, just for convenience: we can use nodes as geometric features
        x0,z0,x1,z1 = rectangle
        return all([self.contains_point((x0,z0)),
                    self.contains_point((x0,z1)),
                    self.contains_point((x1,z0)),
                    self.contains_point((x1,z1))])

    def intersects_rectangle(self, rectangle):
        # untested, just for convenience: we can use nodes as geometric features
        x0,z0,x1,z1 = rectangle
        return any([self.contains_point((x0,z0)),
                    self.contains_point((x0,z1)),
                    self.contains_point((x1,z0)),
                    self.contains_point((x1,z1))])

class TestComplicatedFeature(ut.TestCase):
	def setUp(self):
		geojson = json.load(open("kings-county-1850.geojson"))
		self.feature = module.Feature(geometry=asShape(geojson['features'][0]['geometry']))
		self.inside_point = (1830000, 563000)
		self.outside_point = (1837056, 564700)

	def test_point_inside(self):
		self.failUnless(self.feature.contains_point(self.inside_point))

	def test_point_outside(self):
		self.failIf(self.feature.contains_point(self.outside_point))

	def test_rectangle_intersects(self):
		rectangle = tuple(self.inside_point+self.outside_point)
		self.failUnless(self.feature.intersects_rectangle(rectangle))

	def test_larger_rectangle_intersects(self):
		rectangle = self.feature.geometry.bounds
		self.failUnless(self.feature.intersects_rectangle(
			(rectangle[0]-10, 
				rectangle[1]-10,
				rectangle[2]+10,
				rectangle[3]+10)
			))

	def test_does_not_contain_rectangle(self):
		rectangle = tuple(self.inside_point+self.outside_point)
		self.failIf(self.feature.contains_rectangle(rectangle))

	def test_contains_rectangle(self):
		rectangle = (self.inside_point[0], self.inside_point[1], self.inside_point[0]+10, self.inside_point[1]+10)
		self.failUnless(self.feature.contains_rectangle(rectangle))

class TestSquare(ut.TestCase):
	def setUp(self):
		self.square = module.Feature(Polygon([(0,0), (1,0), (1,1), (0,1)]))

	def test_centroid_is_inside(self):
		self.failUnless(self.square.contains_point((0.5,0.5)))

	def test_side_is_inside(self):
		self.failUnless(self.square.contains_point((0.001,0.5)))

	def test_corner_is_inside(self):
		self.failUnless(self.square.contains_point((0.001,0.001)))

	def test_little_square_inside(self):
		self.failUnless(self.square.contains_rectangle((0.25, 0.25, 0.75, 0.75)))

	def test_offset_square_not_inside(self):
		self.failIf(self.square.contains_rectangle((0.5, 0.5, 1.5, 1.5)))

	def test_offset_square_intersects(self):
		self.failUnless(self.square.intersects_rectangle((0.5, 0.5, 1.5, 1.5)))


class TestNode(ut.TestCase):
	def test_empty_node(self):
		node = module.Node(None, (0,0,1,1))

class TestAddingPoint(ut.TestCase):
	def setUp(self):
		self.node = module.Node(None, (0,0,1,1))
		self.node.add_point((0.5,0.5))

	def test_point_is_inside(self):
		self.failUnless(self.node.contains_point((0.5,0.5)))

	def test_node_is_leaf(self):
		self.assertEqual(self.node.type, module.Node.LEAF)

	def test_one_point(self):
		self.assertEqual(self.node.number_of_points, 1)

	def test_point_is_returned(self):
		self.assertEqual(self.node.points[0], (0.5,0.5))

	def test_outside_point_raises_exception(self):
		def callable():
			self.node.add_point((1.1, 1.1))
		self.assertRaises(Exception, callable)

class TestContains(ut.TestCase):
	def setUp(self):
		self.node = module.Node(None, (0,0,1,1))

	def test_centroid_is_inside(self):
		self.failUnless(self.node.contains_point((0.5,0.5)))

	def test_side_is_inside(self):
		self.failUnless(self.node.contains_point((0,0.5)))

	def test_corner_is_inside(self):
		self.failUnless(self.node.contains_point((0,0)))

class TestSubdivide(ut.TestCase):
	def test_subdivide(self):
		node = module.Node(None, (0,0,1,1), max_points=1)
		node.subdivide()
		self.assertEqual(node.type, module.Node.BRANCH)	

	def test_four_children(self):
		node = module.Node(None, (0,0,1,1), max_points=1)
		node.subdivide()
		self.assertEqual(len(node.children), 4)	

	def test_children_coordinates(self):
		node = module.Node(None, (0,0,1,1), max_points=1)
		node.subdivide()
		children = set([child.rectangle for child in node.children])
		candidates = set([	(0,0,0.5,0.5),
							(0.5,0,1,0.5),
							(0,0.5,0.5,1),
							(0.5,0.5,1,1)])
		self.assertSetEqual(children, candidates)	

	def test_point_count_kept(self):
		node = module.Node(None, (0,0,1,1), max_points=4)
		node.add_point((0.25,0.25))
		node.add_point((0.75,0.25))
		node.add_point((0.25,0.75))
		node.add_point((0.75,0.75))
		old = node.number_of_points
		node.subdivide()
		self.assertEqual(node.number_of_points, old)	

	def test_points_are_split(self):
		node = module.Node(None, (0,0,1,1), max_points=4)
		node.add_point((0.25,0.25))
		node.add_point((0.75,0.25))
		node.add_point((0.25,0.75))
		node.add_point((0.75,0.75))
		node.subdivide()
		for child in node.children:
			self.assertEqual(child.number_of_points, 1)	

class TestAutoSplitting(ut.TestCase):
	def setUp(self):
		self.node = module.Node(None, (0,0,1,1), max_points=1)
		self.node.add_point((0.25,0.25))
		self.node.add_point((0.75,0.75))

	def test_node_is_split(self):
		self.assertEqual(self.node.type, module.Node.BRANCH)

	def test_two_points(self):
		self.assertEqual(self.node.number_of_points, 2)

	def test_both_points_are_inside(self):
		self.failUnless(self.node.contains_point((0.25,0.25)))
		self.failUnless(self.node.contains_point((0.75,0.75)))

	def test_many_points_at_same_location(self):
		self.node.add_point((0.25,0.25))
		self.assertEqual(self.node.number_of_points, 3)

	def test_points_at_same_location_do_not_split(self):
		node = module.Node(None, (0,0,1,1), max_points=1)
		node.add_point((0.25,0.25))
		node.add_point((0.25,0.25))
		self.assertEqual(node.type, module.Node.LEAF)

	def test_points_at_same_location_go_to_same_square(self):
		node = module.Node(None, (0,0,1,1), max_points=1)
		node.add_point((0.25,0.25))
		node.add_point((0.25,0.25))
		node.subdivide()
		self.assertEqual(node.children[0].number_of_points, 2)

class TestFeatureOverlap(ut.TestCase):
	def setUp(self):
		self.square = Feature(None, (0.5, 0.5, 1.5, 1.5))
		self.node = module.Node(None, (0,0,1,1), max_points=3)

	def test_zero_point(self):
		self.assertEqual(self.node.count_overlapping_points(self.square), 0)

	def test_zero_overlap(self):
		self.node.add_point((0.25, 0.25))
		self.assertEqual(self.node.count_overlapping_points(self.square), 0)

	def test_one_of_two_overlap(self):
		self.node.add_point((0.25, 0.25))
		self.node.add_point((0.75, 0.75))
		self.assertEqual(self.node.count_overlapping_points(self.square), 1)

	def test_child_overlaps(self):
		node = self.node
		node.add_point((0.25,0.25))
		node.add_point((0.75,0.25))
		node.add_point((0.25,0.75))
		node.add_point((0.75,0.75))
		self.assertEqual(node.count_overlapping_points(self.square), 1)

	def test_multiple_children_partially_overlap(self):
		node = self.node
		other_square = Feature(None, (0.49, 0.49, 1.49, 1.49))

		node.add_point((0.25,0.25))
		node.add_point((0.75,0.25))
		node.add_point((0.25,0.75))
		node.add_point((0.75,0.75))
		self.assertEqual(node.count_overlapping_points(self.square), 1)

	def test_count(self):
		xs = range(100)
		ys = range(100)
		node = module.Node(None, (0,0,1,1), max_points=1)
		for x in xs:
			for y in ys:
				node.add_point((x/100.0,y/100.0))
		feature = Feature(None, (0.5, 0.5, 1.5, 1.5))
		self.assertEqual(node.count_overlapping_points(feature), 2500)

class TestQuadTree(ut.TestCase):
	def setUp(self):
		self.points = [
			(0,0),
			(0.5,0.5),
			(0.75,0.25),
			(1,1)
		]
		self.quadtree = module.QuadTree(self.points)

	def test_all_points_within_quadtree(self):
		for point in self.points:
			self.failUnless(self.quadtree.contains_point(point))

	def test_rectangle_is_bounding_box(self):
		self.assertEqual(self.quadtree.rectangle, (0,0,1,1))

	def test_has_four_points(self):
		self.assertEqual(self.quadtree.number_of_points, 4)

	def test_known_values(self):
		rectangle = Feature(None, (0.25,0,1.25,0.75))
		self.assertEqual(self.quadtree.count_overlapping_points(rectangle), 2)

class TestWalk(ut.TestCase):
	def test_returns_one_point(self):
		points = [
			(0,0),
		]
		quadtree = module.QuadTree(points)
		self.assertSetEqual(set(quadtree.walk()), set(points))

	def test_returns_four_points(self):
		points = [
			(0,0),
			(0.5,0.5),
			(0.75,0.25),
			(1,1)
		]
		quadtree = module.QuadTree(points)
		self.assertSetEqual(set(quadtree.walk()), set(points))

	def test_returns_many_points(self):
		points = []
		for x in range(100):
			for y in range(100):
				points.append((float(x), float(y)))
		quadtree = module.QuadTree(points)
		self.assertSetEqual(set(quadtree.walk()), set(points))

class TestMetaData(ut.TestCase):
	def setUp(self):
		self.node = module.Node(None, (0,0,1,1), max_points=3)

	def test_add_point_accepts_geometry(self):
		geometry = {"type": "Point", "coordinates": [0.5, 0.5]}
		self.node.add_point(geometry)
		self.assertListEqual(list(self.node.points[0]), [0.5, 0.5])

	def test_add_point_accepts_feature(self):
		feature = {
		  "type": "Feature",
		  "geometry": {
		    "type": "Point",
		    "coordinates": [0.5, 0.5]
		  },
		  "properties": {
		    "name": "Dinagat Islands"
		  }
		}
		self.node.add_point(feature)
		self.assertListEqual(list(self.node.points[0]), [0.5, 0.5])

	def test_get_all_points_returns_feature(self):
		self.node.add_point((0.5, 0.5))
		feature = self.node.get_all_points()[0]
		self.assertEqual(feature['type'], 'Feature')
		self.assertEqual(feature['geometry']['type'], 'Point')
		self.assertListEqual(feature['geometry']['coordinates'], [0.5, 0.5])
		self.failUnless('properties' in feature)

	def test_get_all_points_returns_all(self):
		self.node.add_point((0.5, 0.5))
		self.node.add_point((0.75, 0.75))
		self.assertEqual(self.node.number_of_points, len(self.node.get_all_points()))

	def test_get_all_points_returns_children(self):
		self.node.add_point((0.25, 0.25))
		self.node.add_point((0.75, 0.75))
		self.node.subdivide()
		self.assertEqual(self.node.number_of_points, len(self.node.get_all_points()))

	def test_children_hold_features(self):
		self.node.add_point((0.25, 0.25))
		self.node.add_point((0.75, 0.75))
		self.node.subdivide()
		features = []
		for child in self.node.children:
			features.extend(child.get_all_points())
		self.assertEqual(len(features), 2)

	def test_get_all_points_returns_data(self):
		self.node.add_point((0.5, 0.5))
		input_feature = {
		  "type": "Feature",
		  "geometry": {
		    "type": "Point",
		    "coordinates": [0.5, 0.5]
		  },
		  "properties": {
		    "name": "Dinagat Islands"
		  }
		}
		output_feature = self.node.get_all_points()[0]
		self.assertDictEqual(input_feature, output_feature)

	def test_get_overlapping_points_returns_data(self):
		self.node.add_point((0.25, 0.25))
		input_feature = {
		  "type": "Feature",
		  "geometry": {
		    "type": "Point",
		    "coordinates": [0.75, 0.75]
		  },
		  "properties": {
		    "name": "Dinagat Islands"
		  }
		}
		self.node.add_point(input_feature)
		square = Feature(None, (0.5, 0.5, 1.5, 1.5))
		self.assertDictEqual(input_feature, self.node.get_overlapping_points(square)[0])

	def test_get_overlapping_points_same_as_count(self):
		xs = range(100)
		ys = range(100)
		node = module.Node(None, (0,0,1,1), max_points=1)
		for x in xs:
			for y in ys:
				node.add_point((x/100.0,y/100.0))
		feature = Feature(None, (0.5, 0.5, 1.5, 1.5))
		self.assertEqual(node.count_overlapping_points(feature), len(node.get_overlapping_points(feature)))

	def test_contains_pont_accepts_feature(self):
		input_feature = {
		  "type": "Feature",
		  "geometry": {
		    "type": "Point",
		    "coordinates": [0.5, 0.5]
		  },
		  "properties": {
		    "name": "Dinagat Islands"
		  }
		}
		self.failUnless(self.node.contains_point(input_feature))

	def test_contains_pont_accepts_geometry(self):
		input_feature = {
		    "type": "Point",
		    "coordinates": [0.5, 0.5]
		}
		self.failUnless(self.node.contains_point(input_feature))

if __name__ == '__main__':
	ut.main()