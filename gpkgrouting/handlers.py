"""
"""
import collections
import geopandas as gpd
# import osmium

from osmium import osmium
from shapely import geometry, wkb, wkt

import typing as tp

wktfab = osmium.geom.WKTFactory()
wkbfab = osmium.geom.WKBFactory()

class GeometryHandler(osmium.SimpleHandler):
  def data(self) -> tp.Iterable[tp.Tuple[str, gpd.GeoDataFrame]]:
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
    yield ('ways', gpd.GeoDataFrame.from_records(self.ways))

  def way(self, w: osmium.osm.Way):
    data = wktfab.create_linestring(w)
    geom = wkt.loads(data)
    
    self.ways.append({
      'source': geom.coords[0],
      'target': geom.coords[-1],
      'length': geom.length,
      'geom': geom
    })

class TopologyHandler(osmium.SimpleHandler):
  nodes: gpd.GeoDataFrame = None
  links: gpd.GeoDataFrame = None

  def data(self):
    yield ('nodes', self.nodes)
    yield ('links', self.links)

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
    links = dict()
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
          geom,
        )

        if id not in links:
          links[id] = [edge]
        else:
          links[id].append(edge)

        # Add nodes
        if source not in nodes:
          nodes[source] = wkt.loads(self._nodes[source])
        if target not in nodes:
          nodes[target] = wkt.loads(self._nodes[target])

        source = target
        steps = [target]

    # Flatten data 
    nodes_data = (tuple(x) for x in nodes.items())
    links_data = (x for sublist in links.values() for x in sublist)

    self.nodes = gpd.GeoDataFrame(
      data=nodes_data, 
      columns=['node_id', 'geom'],
      geometry='geom',
      crs={'init':'epsg:4326'},
    )
    self.links = gpd.GeoDataFrame(
      data=links_data, 
      columns=['way_id', 'source', 'target', 'geom'],
      geometry='geom',
      crs={'init':'epsg:4326'},
    )

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
