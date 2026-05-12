import os
import json
import urllib.request
import logging

logger = logging.getLogger(__name__)

REPLICATED_SDK_URL = os.getenv("REPLICATED_SDK_URL", "http://financial-budget-sdk:3000")


def get_license_field(field_name: str):
    """
    Query a single license field from the in-cluster Replicated SDK API.
    Returns the parsed JSON dict or None on error.
    """
    url = f"{REPLICATED_SDK_URL}/api/v1/license/fields/{field_name}"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        logger.warning("Failed to query license field %s: %s", field_name, e)
        return None


def is_custom_categories_enabled() -> bool:
    """
    Check whether the 'custom_category_enabled' license entitlement is active.
    Defaults to False (fail-safe) if the SDK is unreachable or the field
    is not present.
    """
    data = get_license_field("custom_category_enabled")
    if not data:
        return False
    return data.get("value") is True


def get_all_entitlements():
    """
    Return a dict of all license entitlements for the frontend to consume.
    """
    return {
        "custom_category_enabled": is_custom_categories_enabled(),
    }
