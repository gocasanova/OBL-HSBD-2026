hdfs dfs -mkdir -p /lnd/obligatorio_catastro/compressed
hdfs dfs -mkdir -p /raw/obligatorio_catastro/dnc_2026_05
hdfs dfs -mkdir -p /ref/obligatorio_catastro/dnc_2026_05
hdfs dfs -mkdir -p /cur/obligatorio_catastro
hdfs dfs -mkdir -p /anl/obligatorio_catastro

/lnd: zona landing. Guarda el archivo comprimido original descargado desde la fuente.
/raw: zona raw. Guarda los CSV descomprimidos sin modificar.
/ref: zona refined. Guarda los CSV/parquet con columnas nombradas, tipos corregidos y limpieza básica.
/cur: zona curated. Guarda el modelo analítico elegido.
/anl: zona analytics. Guarda resultados de consultas analíticas.