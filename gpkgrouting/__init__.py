import handlers as osmium_handlers

if __name__ == '__main__':
  import typing as tp
  import sys

  from pathlib import Path
  from handlers import GeometryHandler, AllWayHandler, TopologyHandler

  interfaces: tp.List[GeometryHandler] = [
    # AllWayHandler,
    TopologyHandler,
  ]

  default_filename = 'granada-latest-highways.osm.pbf'
  input_filename = input(f'filename (default: {default_filename}): ') or default_filename
  input_path = input_path = Path('../data/').joinpath(input_filename)
  if not input_path.is_file():
    sys.exit('Input file not found')

  print(f'Processing "{input_path.name}" in "{input_path.resolve()}"...')
  for factory in interfaces:
    classname = factory.__name__

    output_filename = input_filename.split('.')[0]
    output_path = Path('./output/').joinpath(classname)
    if not output_path.exists():
      output_path.mkdir()

    print(f'{classname} output of {input_path.name} to {output_path.name}...', end='\r')
      ##
    handler = factory()
    handler.apply_file(str(input_path), locations=True)

    for key, df in handler.data():
      if factory is TopologyHandler:
        df.to_file(output_path.joinpath(f'{output_filename}.gpkg'), include_index=True, driver='GPKG', layer=f'nw_{key}')
      else:
        df.to_csv(output_path.joinpath(f'{output_filename}_{key}.csv'))
      ##
    print(f'{classname} output of {input_path.name} to {output_path.name}... Done!', end='\n')

