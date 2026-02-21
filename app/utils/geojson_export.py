"""
GeoJSON export utility.

Converts query result rows (containing lat/lon columns) into a GeoJSON
FeatureCollection string suitable for use in mapping tools.
"""

import json
from typing import Optional


def _find_col(keys: list[str], candidates: list[str]) -> Optional[str]:
    """Find the first key that matches any candidate substring (case-insensitive)."""
    for k in keys:
        k_lower = k.lower()
        if any(c in k_lower for c in candidates):
            return k
    return None


def rows_to_geojson(
    rows: list[dict],
    lat_col: Optional[str] = None,
    lon_col: Optional[str] = None,
    props_cols: Optional[list[str]] = None,
) -> Optional[str]:
    """
    Convert a list of result dicts to a GeoJSON FeatureCollection string.

    Auto-detects latitude/longitude columns by name if lat_col/lon_col not given.
    Accepts exact column names OR columns containing 'lat'/'lon' as substrings
    (e.g. 'center_lat', 'z.center_lat', 'latitude').

    Args:
        rows: List of dicts from run_query()
        lat_col: Column name containing latitude values (auto-detected if None)
        lon_col: Column name containing longitude values (auto-detected if None)
        props_cols: Columns to include as GeoJSON properties (None = all other cols)

    Returns:
        GeoJSON FeatureCollection as a JSON string, or None if no valid rows found.
    """
    if not rows:
        return None

    keys = list(rows[0].keys())

    # Auto-detect lat/lon columns
    if lat_col is None:
        lat_col = _find_col(keys, ["center_lat", "latitude", "_lat", ".lat"])
    if lon_col is None:
        lon_col = _find_col(keys, ["center_lon", "center_lng", "longitude", "_lon", "_lng", ".lon"])

    if lat_col is None or lon_col is None:
        return None  # No coordinate columns found

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
