# gpkgRouting

gpkgRouting es un programa en Python desarrollado como una prueba de concepto para [mi TFG](https://www.github.com/Alxe/UGR_TFG).

El programa actualmente solo incluye dos clases derivadas de `osm.SimpleHandler` del proyecto [PyOsmium](https://osmcode.org/pyosmium/) que, dado un fichero `example.osm.pbf` (un XML comprimido en protobuf) extraiga los datos de las primitivas _Way_, que representan caminos o líneas, y las almacene en una representación intermediaria, generalmente un _DataFrame_ de [GeoPandas](http://geopandas.org/).

Concretamente, en el fichero `handlers.py` se encuentran dos clases:

* `handlers.AllWayHandler` extrae la información geográfica y calcula su longitud, además de almacenar el nodo de inicio y destino de la primitiva `Way`. Puede considerarse un caso de ejemplo, para ver la funcionalidad de estos.
* `handlers.TopologyHandler` extrae la información geográfica de las primitivas _Way_, almacenando cada nodo usado y cuántas veces se usan. Después, aplica un proceso de normalización en el que subdivide cada enlace en porciones útiles, aquellas que se encuentran entre intersecciones de _Way_. Este es el objeto principal de la prueba de concepto, capaz de leer y crear la topología del fichero original.

Además, en el archivo `__init__.py` en sí, el programa realiza la lectura de un archivo de entrada, genera la topología y la inserta en un archivo _GeoPackage_.

## Limitaciones

Como el trabajo en sí ha sido una demostración específica, el trabajo no está generalizado, aunque sería relativamente trivial insertar argumentos de entrada y salida. Esto es así por diseño.
