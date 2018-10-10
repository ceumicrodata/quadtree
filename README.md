# quadtree

A quadtree implementation in Python to count many points within complex geometric shapes. See `test.py` for more details.

## QuadTree
Build a quadtree from a list of coordinates or a list of geometry features.

```python
from quadtree import QuadTree

feature1 = {
  "type": "Feature",
  "geometry": {
    "type": "Point",
    "coordinates": [0.25, 0.25]
  },
  "properties": {
    "name": "Dinagat Islands"
  }
}
feature2 = {
  "type": "Feature",
  "geometry": {
    "type": "Point",
    "coordinates": [0.75, 0.75]
  },
  "properties": {
    "name": "Dinagat Islands"
  }
}
points = QuadTree([feature1, feature2])
```

### count_overlapping_points
Count the number of points overlapping with your polygon.

```python
from quadtree import Feature
feature = Feature(None, (0.5, 0.5, 1.5, 1.5))
assert points.count_overlapping_points(features) == 1
```

### get_overlapping_points
Count the number of points overlapping with your polygon.

```python
from quadtree import Feature
feature = Feature(None, (0.5, 0.5, 1.5, 1.5))
assert points.get_overlapping_points(features) == [feature2]
```

## Feature
`Feature` is a simple wrapper around Shapely geometry features. It adds three methods that are called by `Quadtree`: `contains_point`, `contains_rectangle` and `intersects_rectangle`. The use of `Feature` is optional, you can use your own geometry class as long as you implement these three methods.

Initialize Feature with a Shapely geometry, or a Python dictionary with a geo interface:

```python
from shapely.geometry import Polygon
from quadtree import Feature
feature = Feature(geometry=Polygon([(0,0), (1,0), (1,1), (0,1)]))
```

### contains_point
`feature.contains_point((x,y))` returns true 
