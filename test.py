import quadtree as module
import unittest as ut

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
		pass

if __name__ == '__main__':
	ut.main()