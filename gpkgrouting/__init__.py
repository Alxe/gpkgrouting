import handlers as osmium_handlers

if __name__ == '__main__':
  from handlers import *

  filename: str = '/home/alejnp/Projects/UGR/TFG/gpkgrouting/data/granada-latest-highways.osm.pbf'
  interfaces: tp.List[AbstractHandler] = [
    AllWayHandler,
    TopologyHandler,
  ]
  
  for interface in interfaces:
    handler = interface()
    handler.apply_file(filename, locations=True)

    for key, df in handler.data():
      df.to_csv(f'output/{interface.__name__}_{key}.csv')
