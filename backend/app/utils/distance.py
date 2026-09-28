import math
from typing import Dict, Tuple

def calculate_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate geographical distance in kilometers between two GPS coordinates using Haversine formula."""
    R = 6371.0 # Earth radius in km
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2.0) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * (math.sin(d_lon / 2.0) ** 2)
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    distance = R * c
    return round(distance, 1)

BLOCK_COORDINATES: Dict[str, Dict[str, float]] = {
    'Moradabad Rural': {'lat': 28.8386, 'lon': 78.7733},
    'Chhajlet': {'lat': 28.9856, 'lon': 78.6811},
    'Bahjoi': {'lat': 28.4000, 'lon': 78.6300},
    'Bilari': {'lat': 28.6256, 'lon': 78.8022},
    'Kundarki': {'lat': 28.7056, 'lon': 78.7844},
    'Bhagatpur Tanda': {'lat': 28.9950, 'lon': 78.9400},
    'Munda Pandey': {'lat': 28.7800, 'lon': 78.9500},
    'District Centre / Industrial Area': {'lat': 28.8350, 'lon': 78.7700}
}

def get_block_coordinates(block_name: str) -> Dict[str, float]:
    return BLOCK_COORDINATES.get(block_name, {'lat': 28.8386, 'lon': 78.7733})
