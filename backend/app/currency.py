import os

# Static lookup table for the currencies offered on the KOTS config screen.
# The operator chooses one via the KOTS dropdown; it flows into the backend
# via CURRENCY_CODE, and the frontend reads /config/currency on load to
# format every amount in the chosen currency.
CURRENCIES = {
    "USD": {
        "code": "USD",
        "symbol": "$",
        "position": "prefix",
        "decimal_places": 2,
        "thousands_sep": ",",
        "decimal_sep": ".",
    },
    "EUR": {
        "code": "EUR",
        "symbol": "€",
        "position": "suffix",
        "decimal_places": 2,
        "thousands_sep": ".",
        "decimal_sep": ",",
    },
    "GBP": {
        "code": "GBP",
        "symbol": "£",
        "position": "prefix",
        "decimal_places": 2,
        "thousands_sep": ",",
        "decimal_sep": ".",
    },
    "JPY": {
        "code": "JPY",
        "symbol": "¥",
        "position": "prefix",
        "decimal_places": 0,
        "thousands_sep": ",",
        "decimal_sep": ".",
    },
    "INR": {
        "code": "INR",
        "symbol": "₹",
        "position": "prefix",
        "decimal_places": 2,
        "thousands_sep": ",",
        "decimal_sep": ".",
    },
}


def get_currency() -> dict:
    code = os.getenv("CURRENCY_CODE", "USD")
    return CURRENCIES.get(code, CURRENCIES["USD"])
