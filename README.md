# Obligatorio DNC + Direcciones + Cartografía

Este repositorio contiene el código y la notebook para construir una base documental que integra:

- Datos Abiertos de la Dirección Nacional de Catastro (DNC).
- Direcciones geográficas de Uruguay.
- Cartografía de padrones urbanos y rurales.

Los datos pesados no se suben al repositorio. Para ejecutar el proyecto en otra computadora hay que copiarlos nuevamente en la estructura indicada abajo.

## Archivos del repo

```text
cargar_datos_dnc.ipynb        Notebook principal del pipeline
base_dnc_documental.py        Funciones para armar documentos de padrones
DOCUMENTACION_NOTEBOOK.md     Explicación detallada de la notebook
comandos.sh                   Comandos auxiliares
MER.png                       Diagrama MER del trabajo
.gitignore                    Exclusiones de datos y salidas
```

## Datos requeridos

Después de clonar el repositorio, crear o copiar la carpeta `Data` con esta estructura:

```text
Data/
  DatosAbiertosDNC(2026-05)/
    Padrones Urbanos.csv
    Padrones Rurales.csv
    Líneas de Construccion.csv
    Histórico de Valores.CSV
    Mutaciones Catastrales.CSV
    Departamentos.csv
    Localidades.csv
    Destinos.csv
    Categorías de Construcción.csv
    Estados de Conservación.csv
    Cubiertas.csv
    Cielorrasos.csv
    Tipos de Obra.csv
    metadatos-dnc-2022-09.pdf

  direccionesDepartamentos/
    artigas.csv
    canelones.csv
    cerro_largo.csv
    colonia.csv
    durazno.csv
    flores.csv
    florida.csv
    lavalleja.csv
    maldonado.csv
    montevideo.csv
    paysandu.csv
    rio_negro.csv
    rivera.csv
    rocha.csv
    salto.csv
    san_jose.csv
    soriano.csv
    tacuarembo.csv
    treinta_y_tres.csv

  shapes/
    paisurbano_shp/
      PaisUrbano.shp
      PaisUrbano.dbf
      PaisUrbano.shx
      PaisUrbano.prj
      ...
    paisrural_shp/
      PaisRural.shp
      PaisRural.dbf
      PaisRural.shx
      PaisRural.prj
      ...
    paislocalidades_shp/
      PaisLocalidades.shp
      ...
    paisseccat_shp/
      PaisSecCat.shp
      ...
```

## Fuentes de datos

Direcciones geográficas:

```text
https://catalogodatos.gub.uy/dataset/ide-direcciones-geograficas-del-uruguay
```

Los datos DNC y los shapefiles deben quedar con los nombres esperados por la notebook. Si cambia algún nombre de archivo, hay que actualizar `TABLES` o las rutas en `cargar_datos_dnc.ipynb`.

## Instalación de dependencias

Abrir la notebook `cargar_datos_dnc.ipynb` y, si faltan dependencias o aparece un error de NumPy/pyarrow, ejecutar:

```python
%pip install --force-reinstall "numpy<2" "pandas<3" "pyarrow<16"
```

Para la parte geográfica:

```python
%pip install geopandas pyogrio
```

Después de instalar, reiniciar el kernel y correr la notebook desde el inicio.

## Ejecución

En la última sección de la notebook se configura la partición a generar:

```python
DEPARTAMENTOS_DIRECCIONES = ["A"]
LIMITE_PADRONES_DIRECCIONES = 1000
```

Esto genera una muestra del departamento `A` con 1000 padrones.

Para procesar todo el departamento:

```python
LIMITE_PADRONES_DIRECCIONES = None
```

Para procesar varios departamentos:

```python
DEPARTAMENTOS_DIRECCIONES = ["A", "B", "C"]
```

## Salidas

La notebook genera archivos en:

```text
salidas/base_direcciones_particionada/
```

La estructura de salida es:

```text
salidas/base_direcciones_particionada/
  departamento=A/
    tipo=urbano/
      part-00000.jsonl
  manifest.csv
```

Estas salidas no se suben al repositorio porque pueden ser pesadas y se pueden regenerar.

## Qué no se sube a Git

El `.gitignore` excluye:

```text
Data/
salidas/
*.zip
__pycache__/
.DS_Store
*_backup_*.ipynb
```

Por eso, al clonar en otra computadora, hay que volver a copiar los datos en `Data/`.

## Resultado esperado

El resultado principal es una base documental en JSONL donde cada documento representa una dirección y contiene un array `padrones` con los padrones asociados por join espacial.

Cada padrón incluido conserva información anidada como:

- Líneas de construcción.
- Histórico de valores.
- Mutaciones catastrales.

Más detalle en:

```text
DOCUMENTACION_NOTEBOOK.md
```
