"""
Kerala Locality Coordinate Matrix and Haversine Distance Engine for Local Hire.
Covers 3 districts: Kollam, Ernakulam, and Thiruvananthapuram.
"""

import math
from typing import Dict, List, Optional, Tuple

# Earth's mean radius in kilometers
EARTH_RADIUS_KM = 6371.0

# Predefined coordinate reference matrix for 3 Kerala districts
LOCALITY_DATA: Dict[str, Tuple[float, float]] = {
    # District: Kollam
    "Chinnakada, Kollam": (8.8856, 76.5864),
    "Kottarakkara, Kollam": (8.9989, 76.7709),
    "Karunagappalli, Kollam": (9.0544, 76.5338),
    "Kundara, Kollam": (8.9602, 76.6822),
    "Paravur, Kollam": (8.8117, 76.6661),

    # District: Ernakulam
    "Kaloor, Ernakulam": (9.9934, 76.2970),
    "Edappally, Ernakulam": (10.0236, 76.3116),
    "Kakkanad, Ernakulam": (10.0159, 76.3419),
    "Aluva, Ernakulam": (10.1076, 76.3516),
    "Fort Kochi, Ernakulam": (9.9658, 76.2421),

    # District: Thiruvananthapuram
    "Palayam, Thiruvananthapuram": (8.5029, 76.9537),
    "Kazhakkoottam, Thiruvananthapuram": (8.5686, 76.8731),
    "Thampanoor, Thiruvananthapuram": (8.4907, 76.9528),
    "Pattom, Thiruvananthapuram": (8.5244, 76.9463),
    "Nedumangad, Thiruvananthapuram": (8.6015, 77.0024),
}

DISTRICTS: List[str] = ["Kollam", "Ernakulam", "Thiruvananthapuram"]

LOCALITIES_BY_DISTRICT: Dict[str, List[str]] = {
    "Kollam": [
        "Chinnakada, Kollam",
        "Kottarakkara, Kollam",
        "Karunagappalli, Kollam",
        "Kundara, Kollam",
        "Paravur, Kollam",
    ],
    "Ernakulam": [
        "Kaloor, Ernakulam",
        "Edappally, Ernakulam",
        "Kakkanad, Ernakulam",
        "Aluva, Ernakulam",
        "Fort Kochi, Ernakulam",
    ],
    "Thiruvananthapuram": [
        "Palayam, Thiruvananthapuram",
        "Kazhakkoottam, Thiruvananthapuram",
        "Thampanoor, Thiruvananthapuram",
        "Pattom, Thiruvananthapuram",
        "Nedumangad, Thiruvananthapuram",
    ],
}

JOB_CATEGORIES: List[str] = [
    "Retail",
    "Hospitality",
    "Telemarketing",
    "Logistics",
    "Events",
]


def calculate_distance(loc1: str, loc2: str) -> Optional[float]:
    """
    Calculates the great-circle distance between two localities in kilometers
    using the Haversine formula on static coordinates.
    Returns distance rounded to 1 decimal place, or None if coordinates are missing.
    """
    if not loc1 or not loc2:
        return None

    if loc1 == loc2:
        return 0.0

    coord1 = LOCALITY_DATA.get(loc1.strip())
    coord2 = LOCALITY_DATA.get(loc2.strip())

    if not coord1 or not coord2:
        return None

    lat1, lon1 = coord1
    lat2, lon2 = coord2

    # Convert decimal degrees to radians
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    # Haversine formula
    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    distance_km = EARTH_RADIUS_KM * c

    return round(distance_km, 1)


def format_distance(distance_km: Optional[float]) -> str:
    """Formats distance for display cards and labels."""
    if distance_km is None:
        return "Distance N/A"
    if distance_km == 0.0:
        return "0.0 km (Same locality)"
    return f"{distance_km:.1f} km away"


def get_district_for_locality(locality: str) -> str:
    """Returns the district name from a locality string or default."""
    for district, loc_list in LOCALITIES_BY_DISTRICT.items():
        if locality in loc_list:
            return district
    if "," in locality:
        parts = locality.split(",")
        return parts[-1].strip()
    return "Ernakulam"

