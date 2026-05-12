import os
import json
import urllib.request
import logging

from app.database import SessionLocal
from app.models import User, Budget, Transaction

logger = logging.getLogger(__name__)


def send_custom_metrics():
    """
    Send aggregate usage metrics to the Replicated SDK.

    This queries the database for count-based totals and POSTs them to
    the in-cluster Replicated SDK API.  If REPLICATED_SDK_URL is not set
    (e.g. local development) this is a no-op.  All errors are caught and
    logged so that metrics never interrupt user-facing flows.
    """
    sdk_url = os.getenv("REPLICATED_SDK_URL")
    if not sdk_url:
        return

    db = None
    try:
        db = SessionLocal()
        users_total = db.query(User).count()
        budgets_total = db.query(Budget).count()
        transactions_total = db.query(Transaction).count()

        payload = json.dumps(
            {
                "data": {
                    "users_total": users_total,
                    "budgets_total": budgets_total,
                    "transactions_total": transactions_total,
                }
            }
        ).encode("utf-8")

        req = urllib.request.Request(
            f"{sdk_url}/api/v1/app/custom-metrics",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=10) as response:
            pass  # response body not needed

        logger.info(
            "Sent custom metrics: users=%d, budgets=%d, transactions=%d",
            users_total,
            budgets_total,
            transactions_total,
        )
    except Exception as e:
        logger.warning("Failed to send custom metrics: %s", e)
    finally:
        if db:
            db.close()
