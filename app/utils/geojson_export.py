"""
GeoJSON export utility.

Converts query result rows (containing lat/lon columns) into a GeoJSON
FeatureCollection string suitable for use in mapping tools.
"""

import json
from typing import Optional


def rows_to_geojson(
    rows: list[dict],
    lat_col: str = "center_lat",
    lon_col: str = "center_lon",
    props_cols: Optional[list[str]] = None,
) -> Optional[str]:
    """
    Convert a list of result dicts to a GeoJSON FeatureCollection string.

    Args:
        rows: List of dicts from run_query()
        lat_col: Column name containing latitude values
        lon_col: Column name containing longitude values
        props_cols: Columns to include as GeoJSON properties (None = all other cols)

    Returns:
        GeoJSON FeatureCollection as a JSON string, or None if no valid rows found.
    """
    features = []
    for row in rows:
        lat = row.get(lat_col)
        lon = row.get(lon_col)
        try:
            lat = float(lat)
            lon = float(lon)
        except (TypeError, ValueError):
            continue  # Skip rows without valid coordinates

        # Determine property columns
        if props_cols is not None:
            props = {k: row[k] for k in props_cols if k in row}
        else:
            props = {k: v for k, v in row.items() if k not in (lat_col, lon_col)}

        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [lon, lat],  # GeoJSON is [longitude, latitude]
            },
            "properties": props,
        })

    if not features:
        return None

    collection = {
        "type": "FeatureCollection",
        "features": features,
    }
    return json.dumps(collection, ensure_ascii=False)
