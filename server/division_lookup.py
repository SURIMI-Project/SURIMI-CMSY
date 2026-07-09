import geopandas as gpd
from shapely.geometry import Point
from pathlib import Path
import logging

# Load the FAO shapefile once when the module is imported
try:
    base_dir = Path(__file__).resolve().parent.parent
    shapefile_path = base_dir / "R_files" / "Shapefile" / "FAO_major_division_37.shp"


    fao_gdf = gpd.read_file(shapefile_path).to_crs(epsg=4326)
    logging.info(f"FAO shapefile loaded with {len(fao_gdf)} records.")
except Exception as e:
    logging.error(f"Could not load FAO shapefile: {e}")
    fao_gdf = None  # Prevent crash; fail gracefully


def get_division(latitude: float, longitude: float) -> str:
    """
    Given latitude and longitude, returns the matching FAO division name.
    Returns 'Unknown Division' if no match is found or data is unavailable.
    """
    if fao_gdf is None:
        return "Unknown Division"

    try:
        point = Point(longitude, latitude)  # [WARNING] Note: (lon, lat) order
        match = fao_gdf[fao_gdf.geometry.contains(point)]

        if not match.empty:
            return match.iloc[0].get("F_NAME", "Unknown Division")

    except Exception as e:
        logging.error(f"get_division failed for ({latitude}, {longitude}): {e}")

    return "Unknown Division"

if __name__ == "__main__":
    # Each tuple: (latitude, longitude)
    test_points = [
        (35.0805, -2.105),   # Example: latitude, longitude
        (35.805, -2.095)
    ]

    logging.info("[TEST] Running FAO division lookup test...\n")
    for lat, lon in test_points:
        result = get_division(lat, lon)
        logging.info(f"Coordinates ({lat}, {lon}) -> Division: {result}")