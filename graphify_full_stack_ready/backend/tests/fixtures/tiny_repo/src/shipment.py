def normalize_lane(lane: str) -> str:
    """Normalize POL/POD lane string."""
    return lane.strip().upper().replace(" ", "-")


def calculate_freight(base: float, surcharge: float) -> float:
    return round(base + surcharge, 2)
