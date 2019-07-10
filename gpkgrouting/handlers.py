"""
"""
import collections
import pandas as pd

from osmium import osmium
from shapely import geometry, ops, wkb, wkt

import typing as tp

wktfab = osmium.geom.WKTFactory()
wkbfab = osmium.geom.WKBFactory()

class AbstractHandler(osmium.SimpleWriter):
  def data(self) -> tp.Iterable[tp.Tuple[str, pd.DataFrame]]:
    raise NotImplementedError

class AllWayHandler(osmium.SimpleHandler):
  """
  Processes all the Way entities into a structured dataframe like:
  - source: id of source node
  - target: id of target node
  - length: length of geometry
  - wkt:    wkt representation of geometry
  """

  ways = []

  def data(self):
    yield ('ways', pd.DataFrame.from_records(self.ways))

  def way(self, w: osmium.osm.Way):
    try:
      data = wktfab.create_linestring(w)
      geom = wkt.loads(data)
      
      self.ways.append({
        'source': geom.coords[0],
        'target': geom.coords[-1],
        'length': geom.length,
        'wkt': geom.to_wkt()
      })
    except RuntimeError as e:
      print(f'Error "{e}" caused by {w}')

class TopologyHandler(osmium.SimpleHandler):
  nodes: pd.DataFrame = None
  edges: pd.DataFrame = None

  def data(self):
    yield ('nodes', self.nodes)
    yield ('edges', self.edges)

  def way(self, w: osmium.osm.Way):
    # Store all node WKB location, tracked by node id
    self._nodes.update({ n.ref : wktfab.create_point(n) for n in w.nodes })

    # Store all node ids on a way, tracked by way id
    self._ways.update({ w.id : [n.ref for n in w.nodes] })

    # Keep a count of used nodes for pruning. Extremities count twice
    self._counter.update((*[n.ref for n in w.nodes], w.nodes[0].ref, w.nodes[-1].ref))
  
  def _normalize(self):
    # Remove unique nodes
    self._counter.subtract(self._counter.keys()) # Remove every key once
    self._counter = +self._counter # Remove less than ones

    nodes = dict()
    edges = dict()
    for id, way in self._ways.items():
      source = way[0]
      steps = [source]
      for target in way[1:]:
        steps.append(target)

        # If target node is not in valid nodes, skip for next
        if target not in self._counter:
          continue

        geom = geometry.LineString([
          wkt.loads(self._nodes[node_id]) for node_id in steps
        ])

        edge = (
          id,
          source,
          target,
          geom.length,
          geom.to_wkt(),
        )

        if id not in edges:
          edges[id] = [edge]
        else:
          edges[id].append(edge)

        # Add nodes
        if source not in nodes:
          nodes[source] = self._nodes[source]
        if target not in nodes:
          nodes[target] = self._nodes[target]

        source = target
        steps = [target]

    edges_data = (x for sublist in edges.values() for x in sublist)

    self.nodes = pd.DataFrame.from_dict(nodes, orient='index', columns=['wkt']).rename_axis('fid')
    self.edges = pd.DataFrame.from_records(edges_data, columns=['fid', 'source', 'target', 'length', 'wkt']).set_index('fid')

  def apply_file(self, *args, **kwargs):
    # Create temporal items to handle topology reading
    self._nodes = dict()
    self._ways = dict()
    self._counter = collections.Counter()
    
    # Parse file (look at `way` method)
    super().apply_file(*args, **kwargs)
    
    # Normalize temporal data
    self._normalize()

    # Delete temporal data references
    del self._nodes
    del self._ways
    del self._counter
