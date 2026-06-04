from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable

import pandas as pd


URBAN_KEY = [
    "codigo_regimen",
    "codigo_departamento",
    "codigo_localidad",
    "nro_padron",
    "block_manzana",
    "ep_ss",
    "unidad",
]

RURAL_KEY = [
    "codigo_departamento",
    "seccion_catastral",
    "nro_padron",
]

RURAL_HISTORICO_KEY = [
    "codigo_departamento",
    "nro_padron",
]

INT_COLUMNS = {
    "nro_padron",
    "seccion_catastral",
    "unidad",
    "area_predio",
    "area_edificada",
    "valor_catastral_terreno",
    "valor_catastral_mejoras",
    "valor_catastral_total",
    "valor_para_impuestos",
    "codigo_destino",
    "tipo_cubierta",
    "indicador_cielorraso",
    "tipo_obra",
    "area_construida",
    "anio_construccion",
    "anio_remanente",
    "unidad_uso_exclusivo",
    "nro_padron_origen",
    "portalNumber",
    "state",
}

FLOAT_COLUMNS = {
    "nivel",
    "categoria_construccion",
    "estado_conservacion",
    "codigo_categoria",
    "codigo_estado",
    "lat",
    "lng",
    "ranking",
}

DATE_COLUMNS = {
    "fecha_ultima_djcu",
    "vigencia_ultima_djcu",
    "fecha_vigencia",
}


def _blank_to_none(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (list, dict, tuple, set)):
        return value
    if isinstance(value, pd.Series):
        return value.dropna().tolist()
    if hasattr(value, "tolist") and not isinstance(value, (str, bytes)):
        converted = value.tolist()
        if isinstance(converted, (list, dict, tuple, set)):
            return converted
        value = converted
    if pd.isna(value):
        return None
    if isinstance(value, str):
        value = value.strip()
        if value in {"", "/  /"}:
            return None
    return value


def _as_key_value(value: Any) -> str:
    value = _blank_to_none(value)
    return "" if value is None else str(value)


def make_key(row: pd.Series | dict[str, Any], key_cols: list[str]) -> tuple[str, ...]:
    return tuple(_as_key_value(row.get(col)) for col in key_cols)


def _to_int(value: Any) -> int | None:
    value = _blank_to_none(value)
    if value is None:
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _to_float(value: Any) -> float | None:
    value = _blank_to_none(value)
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_iso_date(value: Any) -> str | None:
    value = _blank_to_none(value)
    if value is None:
        return None
    parsed = pd.to_datetime(value, dayfirst=True, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed.date().isoformat()


def clean_record(record: dict[str, Any]) -> dict[str, Any]:
    cleaned = {}
    for col, value in record.items():
        if col in INT_COLUMNS:
            cleaned[col] = _to_int(value)
        elif col in FLOAT_COLUMNS:
            cleaned[col] = _to_float(value)
        elif col in DATE_COLUMNS:
            cleaned[col] = _to_iso_date(value)
        else:
            cleaned[col] = _blank_to_none(value)
    return cleaned


def compact_record(record: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in clean_record(record).items() if value is not None}


def catalog_map(df: pd.DataFrame, code_col: str = None, label_col: str = "denominacion") -> dict[str, str]:
    if code_col is None:
        code_col = df.columns[0]
    return {
        _as_key_value(row[code_col]): row[label_col]
        for _, row in df.iterrows()
        if _blank_to_none(row.get(code_col)) is not None
    }


def preparar_dimensiones(
    departamentos: pd.DataFrame,
    localidades: pd.DataFrame,
    destinos: pd.DataFrame,
    categorias_construccion: pd.DataFrame,
    estados_conservacion: pd.DataFrame,
    cubiertas: pd.DataFrame,
    cielorrasos: pd.DataFrame,
    tipos_obra: pd.DataFrame,
) -> dict[str, dict[Any, str]]:
    return {
        "departamentos": catalog_map(departamentos, "codigo_departamento"),
        "localidades": {
            (
                _as_key_value(row["codigo_departamento"]),
                _as_key_value(row["codigo_localidad"]),
            ): row["denominacion"]
            for _, row in localidades.iterrows()
        },
        "destinos": catalog_map(destinos, "codigo_destino"),
        "categorias_construccion": catalog_map(categorias_construccion, "codigo_categoria"),
        "estados_conservacion": catalog_map(estados_conservacion, "codigo_estado"),
        "cubiertas": catalog_map(cubiertas, "codigo_cubierta"),
        "cielorrasos": catalog_map(cielorrasos, "codigo_cielorraso"),
        "tipos_obra": catalog_map(tipos_obra, "codigo_tipo_obra"),
    }


def enriquecer_padrones_urbanos(padrones_urbanos: pd.DataFrame, dims: dict[str, dict[Any, str]]) -> pd.DataFrame:
    df = padrones_urbanos.copy()
    df["departamento"] = df["codigo_departamento"].map(dims["departamentos"])
    df["localidad"] = df.apply(
        lambda row: dims["localidades"].get((row["codigo_departamento"], row["codigo_localidad"])),
        axis=1,
    )
    return df


def enriquecer_padrones_rurales(padrones_rurales: pd.DataFrame, dims: dict[str, dict[Any, str]]) -> pd.DataFrame:
    df = padrones_rurales.copy()
    df["departamento"] = df["codigo_departamento"].map(dims["departamentos"])
    return df


def enriquecer_lineas_construccion(lineas_construccion: pd.DataFrame, dims: dict[str, dict[Any, str]]) -> pd.DataFrame:
    df = lineas_construccion.copy()
    df["destino"] = df["codigo_destino"].map(dims["destinos"])
    df["categoria_construccion_nombre"] = df["categoria_construccion"].map(dims["categorias_construccion"])
    df["estado_conservacion_nombre"] = df["estado_conservacion"].map(dims["estados_conservacion"])
    df["tipo_cubierta_nombre"] = df["tipo_cubierta"].map(dims["cubiertas"])
    df["cielorraso_nombre"] = df["indicador_cielorraso"].map(dims["cielorrasos"])
    df["tipo_obra_nombre"] = df["tipo_obra"].map(dims["tipos_obra"])
    return df


def historico_valores_a_array(row: pd.Series) -> list[dict[str, Any]]:
    valores = []
    for offset in range(1, 5):
        valores.append(
            {
                "anio_offset": offset,
                "periodo": f"anio_-{offset}",
                "valor_catastral": _to_int(row.get(f"valor_catastral_anio_{offset}")),
                "valor_impuestos": _to_int(row.get(f"valor_impuestos_anio_{offset}")),
            }
        )

    for index, actual in enumerate(valores):
        anterior_disponible = valores[index + 1] if index + 1 < len(valores) else None
        if anterior_disponible is None:
            actual["cambio_catastral_vs_anio_anterior_disponible"] = None
            actual["cambio_impuestos_vs_anio_anterior_disponible"] = None
            actual["cambio_pct_catastral_vs_anio_anterior_disponible"] = None
            actual["cambio_pct_impuestos_vs_anio_anterior_disponible"] = None
            continue

        for prefix, field in [
            ("catastral", "valor_catastral"),
            ("impuestos", "valor_impuestos"),
        ]:
            current_value = actual[field]
            previous_value = anterior_disponible[field]
            change_key = f"cambio_{prefix}_vs_anio_anterior_disponible"
            pct_key = f"cambio_pct_{prefix}_vs_anio_anterior_disponible"
            if current_value is None or previous_value in {None, 0}:
                actual[change_key] = None
                actual[pct_key] = None
            else:
                actual[change_key] = current_value - previous_value
                actual[pct_key] = (current_value / previous_value) - 1

    return [compact_record(item) for item in valores]


def mutacion_a_record(row: pd.Series) -> dict[str, Any]:
    record = compact_record(row.to_dict())
    fecha = _to_iso_date(row.get("fecha_vigencia"))
    record["fecha_vigencia"] = fecha
    record["anio_vigencia"] = int(fecha[:4]) if fecha else None
    return compact_record(record)


def linea_construccion_a_record(row: pd.Series) -> dict[str, Any]:
    skip_cols = set(URBAN_KEY)
    return compact_record({col: value for col, value in row.to_dict().items() if col not in skip_cols})


def _filter_by_keys(df: pd.DataFrame, key_df: pd.DataFrame, key_cols: list[str]) -> pd.DataFrame:
    keys = key_df[key_cols].drop_duplicates()
    return df.merge(keys, on=key_cols, how="inner")


def agrupar_registros(
    df: pd.DataFrame,
    key_cols: list[str],
    builder: Callable[[pd.Series], dict[str, Any] | list[dict[str, Any]]],
) -> dict[tuple[str, ...], list[dict[str, Any]]]:
    grouped = defaultdict(list)
    for _, row in df.iterrows():
        key = make_key(row, key_cols)
        record = builder(row)
        if isinstance(record, list):
            grouped[key].extend(record)
        else:
            grouped[key].append(record)
    return dict(grouped)


def id_padron_urbano(row: pd.Series) -> str:
    return "URB|" + "|".join(make_key(row, URBAN_KEY))


def id_padron_rural(row: pd.Series) -> str:
    return "RUR|" + "|".join(make_key(row, RURAL_KEY))


def construir_base_padrones_urbanos(
    padrones_urbanos: pd.DataFrame,
    lineas_construccion: pd.DataFrame,
    historico_valores: pd.DataFrame,
    mutaciones_catastrales: pd.DataFrame,
    dims: dict[str, dict[Any, str]],
    limite: int | None = 1000,
    incluir_lineas: bool = True,
) -> pd.DataFrame:
    padrones = enriquecer_padrones_urbanos(padrones_urbanos, dims)
    if limite is not None:
        padrones = padrones.head(limite).copy()

    historico_urbano = historico_valores[historico_valores["codigo_regimen"].isin(["CO", "PH", "UH"])]
    historico_urbano = _filter_by_keys(historico_urbano, padrones, URBAN_KEY)
    historico_lookup = agrupar_registros(historico_urbano, URBAN_KEY, historico_valores_a_array)

    mutaciones_urbanas = mutaciones_catastrales[mutaciones_catastrales["codigo_regimen"].isin(["CO", "PH", "UH"])]
    mutaciones_urbanas = _filter_by_keys(mutaciones_urbanas, padrones, URBAN_KEY)
    mutaciones_lookup = agrupar_registros(mutaciones_urbanas, URBAN_KEY, mutacion_a_record)

    if incluir_lineas:
        lineas = enriquecer_lineas_construccion(lineas_construccion, dims)
        lineas = _filter_by_keys(lineas, padrones, URBAN_KEY)
        lineas_lookup = agrupar_registros(lineas, URBAN_KEY, linea_construccion_a_record)
    else:
        lineas_lookup = {}

    documentos = []
    for _, row in padrones.iterrows():
        key = make_key(row, URBAN_KEY)
        documento = clean_record(row.to_dict())
        documento["id_padron_documental"] = id_padron_urbano(row)
        documento["tipo_padron"] = "urbano"
        documento["lineas_construccion"] = lineas_lookup.get(key, [])
        documento["historico_valores"] = historico_lookup.get(key, [])
        documento["mutaciones"] = mutaciones_lookup.get(key, [])
        documentos.append(documento)

    return pd.DataFrame(documentos)


def construir_base_padrones_rurales(
    padrones_rurales: pd.DataFrame,
    historico_valores: pd.DataFrame,
    mutaciones_catastrales: pd.DataFrame,
    dims: dict[str, dict[Any, str]],
    limite: int | None = 1000,
) -> pd.DataFrame:
    padrones = enriquecer_padrones_rurales(padrones_rurales, dims)
    if limite is not None:
        padrones = padrones.head(limite).copy()

    historico_rural = historico_valores[historico_valores["codigo_regimen"].eq("RU")]
    historico_rural = _filter_by_keys(historico_rural, padrones, RURAL_HISTORICO_KEY)
    historico_lookup = agrupar_registros(historico_rural, RURAL_HISTORICO_KEY, historico_valores_a_array)

    mutaciones_rurales = mutaciones_catastrales[mutaciones_catastrales["codigo_regimen"].eq("RU")]
    mutaciones_rurales = _filter_by_keys(mutaciones_rurales, padrones, RURAL_KEY)
    mutaciones_lookup = agrupar_registros(mutaciones_rurales, RURAL_KEY, mutacion_a_record)

    documentos = []
    for _, row in padrones.iterrows():
        key = make_key(row, RURAL_KEY)
        hist_key = make_key(row, RURAL_HISTORICO_KEY)
        documento = clean_record(row.to_dict())
        documento["id_padron_documental"] = id_padron_rural(row)
        documento["tipo_padron"] = "rural"
        documento["lineas_construccion"] = []
        documento["historico_valores"] = historico_lookup.get(hist_key, [])
        documento["mutaciones"] = mutaciones_lookup.get(key, [])
        documentos.append(documento)

    return pd.DataFrame(documentos)


def exportar_jsonl(df: pd.DataFrame, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for record in df.to_dict(orient="records"):
            file.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
    return path


def resumen_base_documental(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "documentos": [len(df)],
            "con_lineas_construccion": [df["lineas_construccion"].map(bool).sum()],
            "con_historico_valores": [df["historico_valores"].map(bool).sum()],
            "con_mutaciones": [df["mutaciones"].map(bool).sum()],
            "lineas_construccion_total": [df["lineas_construccion"].map(len).sum()],
            "historico_valores_total": [df["historico_valores"].map(len).sum()],
            "mutaciones_total": [df["mutaciones"].map(len).sum()],
        }
    )
