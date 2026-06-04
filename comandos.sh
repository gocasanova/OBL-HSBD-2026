hdfs dfs -mkdir -p /lnd
hdfs dfs -mkdir -p /raw
hdfs dfs -mkdir -p /ref
hdfs dfs -mkdir -p /cur
hdfs dfs -mkdir -p /anl

/lnd: zona landing. Guarda el archivo comprimido original descargado desde la fuente.
/raw: zona raw. Guarda los CSV descomprimidos sin modificar.
/ref: zona refined. Guarda los CSV/parquet con columnas nombradas, tipos corregidos y limpieza básica.
/cur: zona curated. Guarda el modelo analítico elegido.
/anl: zona analytics. Guarda resultados de consultas analíticas.