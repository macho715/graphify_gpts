from .shipment import normalize_lane


class InvoiceValidator:
    """Validates invoice amount and shipment lane evidence."""

    def __init__(self, tolerance: float = 0.01) -> None:
        self.tolerance = tolerance

    def validate_invoice(self, amount: float, expected: float, lane: str) -> bool:
        lane_code = normalize_lane(lane)
        return abs(amount - expected) <= self.tolerance and bool(lane_code)


def validate_invoice(amount: float, expected: float, lane: str) -> bool:
    validator = InvoiceValidator()
    return validator.validate_invoice(amount, expected, lane)
