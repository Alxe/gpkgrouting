#!/usr/bin/env python3

from typing import Callable, Dict, Any
from osgeo import ogr,  osr
from itertools import count
import csv

# Spatial Reference System (default: EPSG 4326)
_srs = osr.SpatialReference()
_srs.ImportFromEPSG(4326)

# field definition
_attributes = {
  'nodes' : [ 
    ('id', ogr.OFTInteger64), 
    ],
  'edges' : [ 
    ('id', ogr.OFTInteger64), 
    ('source', ogr.OFTInteger64),
    ('target', ogr.OFTInteger64),
    ('length', ogr.OFTReal),
    ('foot', ogr.OFTInteger64),
    ('car_forward', ogr.OFTInteger64),
    ('car_backward', ogr.OFTInteger64),
    ('bike_forward', ogr.OFTInteger64),
    ('bike_backward', ogr.OFTInteger64),
    ],
}

# table definition : [field definition ...]
tables = {
  ('nodes', _srs, ogr.wkbPoint) : _attributes['nodes'],
  ('edges', _srs, ogr.wkbLineString) : _attributes['edges'],
}

# fill layer
def fill_layer(layer_name: str, geom_cb: Callable[[Dict[Any, Any]], str]):
  layer = gpkg.GetLayerByName(layer_name)
  for (i, row) in zip(count(), csv.DictReader(open(f'{layer_name}.csv'))):
    feat = ogr.Feature(layer.GetLayerDefn())
    
    # Geometry
    geom = ogr.CreateGeometryFromWkt(geom_cb(row))
    feat.SetGeometry(geom)

    # Attributes
    for (attr_name, *_) in _attributes[layer_name]:
      feat.SetField(attr_name, row[attr_name])
    
    layer.CreateFeature(feat)
    #print(f"{layer_name}: Feature {i}", end='\r')
  #print()

if __name__ == '__main__':
  import sys

  input_file = sys.argv[1]

  # 1. Create the GeoPackage
  print("Creating the GeoPackage: ...", end='\r')
  driver = ogr.GetDriverByName('GPKG')
  gpkg = driver.CreateDataSource(input_file)

  for (table_defn, field_defn) in tables.items():
    layer = gpkg.CreateLayer(*table_defn)

    for f in field_defn:
      layer.CreateField(ogr.FieldDefn(*f))
  print("Creating the GeoPackage: done")
  # 2. Populate Nodes
  print("Populating nodes: ...", end='\r')
  fill_layer('nodes', geom_cb=lambda r: f'POINT ({r["lon"]} {r["lat"]})')
  print("Populating nodes: done")

  # 3. Populate Edges
  print("Populating edges: ...", end='\r')
  fill_layer('edges', geom_cb=lambda r: r['wkt'])
  print("Populating edges: done")