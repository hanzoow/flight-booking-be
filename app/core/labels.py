AIRLINES: dict[str, str] = {
    "MH": "Malaysia Airlines",
    "AK": "AirAsia",
    "SQ": "Singapore Airlines",
    "TR": "Scoot",
    "TG": "Thai Airways",
    "QF": "Qantas",
    "CX": "Cathay Pacific",
    "JL": "Japan Airlines",
    "KE": "Korean Air",
}

CABINS: dict[str, str] = {
    "Y": "Economy",
    "W": "Premium Economy",
    "J": "Business",
    "F": "First",
}

BOOKING_STATUS: dict[str, str] = {
    "HK": "Confirmed",
    "HL": "Waitlisted",
    "HN": "Holding need",
    "UC": "Unable to confirm",
    "UN": "Unable — no seats",
    "NO": "No action taken",
}

PASSENGER_TYPES: dict[str, str] = {
    "ADT": "Adult",
    "CHD": "Child",
    "INF": "Infant",
}

TAX_CODES: dict[str, str] = {
    "YR": "Fuel surcharge",
    "YQ": "Carrier-imposed charge",
    "SG": "Singapore airport charge",
    "OB": "Airport / security fee",
    "GB": "Government / regulatory fee",
    "UB": "Passenger service charge",
    "D8": "Discount / adjustment",
}


def aircraft_label(code: str | None) -> str | None:
    if not code:
        return None
    mapping = {
        "738": "Boeing 737-800",
        "739": "Boeing 737-900",
        "320": "Airbus A320",
        "321": "Airbus A321",
        "333": "Airbus A330-300",
        "359": "Airbus A350-900",
        "388": "Airbus A380",
        "77W": "Boeing 777-300ER",
    }
    return mapping.get(code.upper(), f"Aircraft {code}")


def payment_method_label(code: str) -> str:
    return {
        "CC": "Credit card",
        "DC": "Debit card",
        "BT": "Bank transfer",
    }.get(code, code)
