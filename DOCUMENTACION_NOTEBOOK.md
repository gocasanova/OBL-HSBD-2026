# Documentación de `cargar_datos_dnc.ipynb`

## Objetivo

La notebook construye una base documental que integra:

- Datos Abiertos de la Dirección Nacional de Catastro (DNC).
- Direcciones geográficas descargadas del catálogo de datos abiertos.
- Cartografía de padrones urbanos y rurales.

El resultado final es una base en formato JSONL particionada por departamento y tipo de padrón, donde cada documento representa una dirección y contiene, dentro de un array, el o los padrones asociados por join espacial.

## Fuentes de datos

La notebook usa estas carpetas:

```text
Data/DatosAbiertosDNC(2026-05)
Data/direccionesDepartamentos
Data/shapes
```

### Datos Abiertos DNC

Contiene archivos CSV sin header. La notebook asigna los nombres de columnas según los metadatos de DNC.

Tablas principales:

- `Padrones Urbanos.csv`
- `Padrones Rurales.csv`
- `Líneas de Construccion.csv`
- `Histórico de Valores.CSV`
- `Mutaciones Catastrales.CSV`

Tablas auxiliares:

- `Departamentos.csv`
- `Localidades.csv`
- `Destinos.csv`
- `Categorías de Construcción.csv`
- `Estados de Conservación.csv`
- `Cubiertas.csv`
- `Cielorrasos.csv`
- `Tipos de Obra.csv`

### Direcciones geográficas

Los archivos están en:

```text
Data/direccionesDepartamentos
```

Son CSV por departamento, descargados desde:

```text
https://catalogodatos.gub.uy/dataset/ide-direcciones-geograficas-del-uruguay
```

Cada registro tiene datos como latitud, longitud, vía, número de puerta, localidad, código postal y departamento.

### Shapes

Los shapefiles están en:

```text
Data/shapes
```

Capas usadas:

- `PaisUrbano`: polígonos de padrones urbanos.
- `PaisRural`: polígonos de padrones rurales.

## Qué hace la notebook

### 1. Configura entorno y rutas

Define las rutas principales:

```python
DATA_DIR = Path("Data/DatosAbiertosDNC(2026-05)")
DIRECCIONES_DIR = Path("Data/direccionesDepartamentos")
SHAPES_DIR = Path("Data/shapes")
OUTPUT_DIR = Path("salidas")
```

También incluye celdas opcionales para instalar dependencias si el entorno tiene problemas con `pandas`, `numpy`, `pyarrow` o `geopandas`.

### 2. Carga los datos DNC

La notebook define un diccionario `TABLES` con el nombre de cada archivo y sus columnas.

Luego carga cada CSV con:

```python
read_csv_with_header(...)
```

Los datos se cargan como texto (`dtype=str`) para preservar códigos, blancos y formatos originales.

Al terminar, crea variables como:

```python
padrones_urbanos
padrones_rurales
lineas_construccion
historico_valores
mutaciones_catastrales
departamentos
localidades
```

También genera:

```python
resumen_dnc
```

con filas, columnas, archivo y encoding usado.

### 3. Prepara dimensiones y documentos de padrones

Usa el módulo:

```python
base_dnc_documental.py
```

Este módulo permite construir documentos de padrón con información anidada.

Cada padrón puede incluir:

```python
lineas_construccion
historico_valores
mutaciones
```

La notebook prepara el diccionario:

```python
dimensiones_dnc
```

que sirve para agregar nombres descriptivos a códigos de departamento, localidad, destino, categoría, estado de conservación, cubierta, cielorraso y tipo de obra.

### 4. Carga direcciones por departamento

La notebook no carga todas las direcciones del país de una sola vez.

En cambio, para cada partición lee únicamente el CSV del departamento necesario:

```python
leer_direcciones_departamento(codigo_departamento)
```

También limpia duplicados de direcciones con:

```python
limpiar_duplicados_direcciones(...)
```

La limpieza:

- Elimina duplicados exactos.
- Normaliza texto de vía, localidad y número.
- Normaliza coordenadas.
- Conserva el registro más completo cuando hay duplicados por dirección.

### 5. Carga cartografía bajo demanda

Los shapefiles se cargan solo cuando se necesitan:

```python
cargar_shape_si_falta("PaisUrbano")
cargar_shape_si_falta("PaisRural")
```

Las claves usadas para cruzar con DNC son:

Urbanos:

```text
CODDEPTO
CODLOCCAT
PADRON
```

Rurales:

```text
CODDEPTO
SECCAT
PADRON
```

### 6. Hace join espacial entre direcciones y padrones

La notebook convierte las direcciones en puntos geográficos:

```python
direcciones_a_geodataframe(...)
```

Luego usa `geopandas.sjoin` para asignar direcciones a padrones:

```python
gpd.sjoin(..., predicate="intersects")
```

La regla es:

```text
si el punto de dirección intersecta el polígono del padrón,
entonces esa dirección queda asociada a ese padrón.
```

### 7. Construye la gran base documental

La función principal es:

```python
construir_base_direcciones_particionada(...)
```

Genera documentos centrados en direcciones.

Cada documento queda con esta estructura conceptual:

```json
{
  "direccion": "...",
  "latitud_num": -34.0,
  "longitud_num": -56.0,
  "localidad": "...",
  "departamento": "...",
  "tipo_padron_match": "urbano",
  "cantidad_padrones": 1,
  "padrones": [
    {
      "codigo_departamento": "...",
      "codigo_localidad": "...",
      "nro_padron": "...",
      "valor_catastral_total": "...",
      "lineas_construccion": [],
      "historico_valores": [],
      "mutaciones": []
    }
  ]
}
```

## Salidas

La salida se escribe en:

```text
salidas/base_direcciones_particionada
```

Con estructura particionada:

```text
salidas/base_direcciones_particionada/
  departamento=A/
    tipo=urbano/
      part-00000.jsonl
  manifest.csv
```

El archivo:

```text
manifest.csv
```

resume cada partición generada:

- Departamento.
- Tipo de padrón.
- Cantidad de documentos.
- Cantidad de padrones en shape.
- Cantidad de direcciones candidatas.
- Cantidad de matches espaciales.
- Ruta del archivo JSONL generado.

## Cómo ejecutar

La ejecución se configura en la última sección:

```python
DEPARTAMENTOS_DIRECCIONES = ["A"]
LIMITE_PADRONES_DIRECCIONES = 1000
```

Esto genera una muestra para el departamento `A`, que corresponde a Canelones, limitada a 1000 padrones.

Para procesar todo el departamento:

```python
LIMITE_PADRONES_DIRECCIONES = None
```

Para procesar varios departamentos:

```python
DEPARTAMENTOS_DIRECCIONES = ["A", "B", "C"]
```

Para incluir rurales:

```python
manifest_base_direcciones = construir_base_direcciones_particionada(
    codigos_departamento=DEPARTAMENTOS_DIRECCIONES,
    limite_padrones_por_departamento=LIMITE_PADRONES_DIRECCIONES,
    incluir_urbano=True,
    incluir_rural=True,
)
```

## Consideraciones

- `PaisUrbano` y `PaisRural` son capas grandes, por lo que cargar todo el país puede consumir memoria.
- Se recomienda procesar por departamento.
- El join espacial depende de que las direcciones tengan coordenadas correctas.
- Una dirección puede caer en más de un polígono si hay geometrías superpuestas.
- Algunos padrones pueden no recibir dirección si no hay un punto de dirección dentro del polígono.
- Para padrones rurales puede haber menos matches porque las direcciones geográficas son más densas en zonas urbanas.

## Archivos relacionados

```text
cargar_datos_dnc.ipynb
base_dnc_documental.py
cargar_datos_dnc_backup_limpieza.ipynb
```

El backup conserva la versión exploratoria anterior de la notebook.
