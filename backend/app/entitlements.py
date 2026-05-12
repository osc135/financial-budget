import os
import json
import urllib.request
import logging
from datetime import datetime, timezone

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


def get_license_status() -> dict:
    """
    Query the Replicated SDK for the 'expires_at' license field and
    determine whether the license is currently valid.

    Returns a dict with keys:
      - valid: bool
      - expires_at: str | None (ISO date string, or None if never expires)
      - reason: str | None (human-readable explanation when invalid)
    """
    data = get_license_field("expires_at")
    if not data:
        return {
            "valid": False,
            "expires_at": None,
            "reason": "Unable to verify license. Please contact support.",
        }

    value = data.get("value", "")
    # Empty string means the license never expires
    if value == "" or value is None:
        return {"valid": True, "expires_at": None, "reason": None}

    try:
        expires = datetime.fromisoformat(value.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        if now > expires:
            return {
                "valid": False,
                "expires_at": value,
                "reason": "License expired. Please contact support to renew your license.",
            }
        return {"valid": True, "expires_at": value, "reason": None}
    except Exception:
        return {
            "valid": False,
            "expires_at": value,
            "reason": "Invalid license expiration format. Please contact support.",
        }


def is_license_valid() -> bool:
    """Short-hand that returns True only when the license is currently valid."""
    return get_license_status().get("valid", False)


def get_available_updates() -> dict:
    """
    Query the Replicated SDK for the current release and any available
    updates on the channel.

    Returns a dict with keys:
      - update_available: bool
      - current_version: str
      - available_version: str | None
    """
    try:
        # Current release info
        info_url = f"{REPLICATED_SDK_URL}/api/v1/app/info"
        req = urllib.request.Request(info_url, method="GET")
        with urllib.request.urlopen(req, timeout=5) as response:
            info = json.loads(response.read().decode("utf-8"))
        current_version = info.get("currentRelease", {}).get("versionLabel", "unknown")

        # Pending updates
        updates_url = f"{REPLICATED_SDK_URL}/api/v1/app/updates"
        req = urllib.request.Request(updates_url, method="GET")
        with urllib.request.urlopen(req, timeout=5) as response:
            updates = json.loads(response.read().decode("utf-8"))

        if updates and len(updates) > 0:
            return {
                "update_available": True,
                "current_version": current_version,
                "available_version": updates[0].get("versionLabel", "unknown"),
            }
        return {
            "update_available": False,
            "current_version": current_version,
            "available_version": None,
        }
    except Exception as e:
        logger.warning("Failed to check for available updates: %s", e)
        return {
            "update_available": False,
            "current_version": "unknown",
            "available_version": None,
        }
