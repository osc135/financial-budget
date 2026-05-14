import logging
import threading

# Ensure warnings are visible in container logs (Python's default is to
# silently discard them if no handler is configured).
logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Annotated
from datetime import timedelta

from app.database import engine, Base, get_db
from app.models import User, Budget, Transaction
from app.schemas import (
    UserCreate, UserResponse, Token,
    BudgetCreate, BudgetResponse,
    TransactionCreate, TransactionResponse,
    DashboardData
)
from app.auth import (
    get_password_hash, verify_password, create_access_token,
    get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES
)
from app.cache import (
    get_dashboard_cache, set_dashboard_cache, invalidate_dashboard_cache
)
from app.metrics import send_custom_metrics
from app.entitlements import (
    is_custom_categories_enabled, get_all_entitlements,
    get_license_status, is_license_valid, get_available_updates,
)
import os
import time

from kubernetes import client as k8s_client, config as k8s_config
from kubernetes.client.rest import ApiException

logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Financial Budget API")

# Start a background thread that periodically queries the license
# so that license connectivity failures are logged even when no user
# requests are being made.
def _license_check_loop():
    while True:
        try:
            get_license_status()
        except Exception:
            pass
        time.sleep(10)

threading.Thread(target=_license_check_loop, daemon=True).start()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def require_valid_license():
    """
    FastAPI dependency that raises 403 Forbidden when the license is
    expired or otherwise invalid. Applied to all protected routes so
    the app actively blocks access when the license is not valid.
    """
    status_info = get_license_status()
    if not status_info.get("valid", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=status_info.get(
                "reason", "License expired or invalid. Please contact support to renew your license."
            ),
        )


@app.get("/")
def root():
    return {"message": "Financial Budget API"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED,
          dependencies=[Depends(require_valid_license)])
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already registered")
    new_user = User(
        username=user.username,
        password_hash=get_password_hash(user.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    threading.Thread(target=send_custom_metrics, daemon=True).start()
    return new_user


@app.post("/auth/login", dependencies=[Depends(require_valid_license)])
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": str(user.id)}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer", "user": {"id": user.id, "username": user.username}}


@app.get("/license/entitlements")
def license_entitlements():
    """Return current license entitlements for the frontend."""
    return get_all_entitlements()


@app.get("/license/status")
def license_status():
    """Return the current license validity status for the frontend banner."""
    return get_license_status()


@app.get("/license/updates")
def license_updates():
    """Return whether a newer release is available on the channel."""
    return get_available_updates()


@app.post("/support-bundle/generate", status_code=status.HTTP_202_ACCEPTED)
def generate_support_bundle(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Create a Kubernetes Job that collects a support bundle and uploads
    it to the Vendor Portal via the Replicated SDK."""
    try:
        k8s_config.load_incluster_config()
    except k8s_config.ConfigException:
        k8s_config.load_kube_config()

    namespace = os.environ.get("POD_NAMESPACE", "default")
    runner_sa = os.environ.get("SUPPORT_BUNDLE_RUNNER_SA", "financial-budget-bundle-runner")
    sdk_url = os.environ.get("REPLICATED_SDK_URL", "http://financial-budget-sdk:3000")

    upload_cmd = (
        "curl -fsS -X POST "
        "-H 'Content-Type: application/gzip' "
        f"--data-binary @/data/bundle.tar.gz "
        f"{sdk_url}/api/v1/supportbundle"
    )

    job_manifest = {
        "apiVersion": "batch/v1",
        "kind": "Job",
        "metadata": {
            "generateName": "support-bundle-",
            "namespace": namespace,
            "labels": {"app.kubernetes.io/component": "support-bundle-runner"},
        },
        "spec": {
            "backoffLimit": 0,
            "ttlSecondsAfterFinished": 600,
            "template": {
                "metadata": {
                    "labels": {"app.kubernetes.io/component": "support-bundle-runner"},
                },
                "spec": {
                    "serviceAccountName": runner_sa,
                    "restartPolicy": "Never",
                    "initContainers": [
                        {
                            "name": "collect",
                            "image": "replicated/troubleshoot:latest",
                            "command": ["/troubleshoot/support-bundle"],
                            "args": [
                                "--interactive=false",
                                "--selector", "troubleshoot.sh/kind=support-bundle",
                                "-o", "/data/bundle.tar.gz",
                            ],
                            "volumeMounts": [{"name": "data", "mountPath": "/data"}],
                        },
                    ],
                    "containers": [
                        {
                            "name": "upload",
                            "image": "curlimages/curl:8.5.0",
                            "command": ["sh", "-c"],
                            "args": [upload_cmd],
                            "volumeMounts": [{"name": "data", "mountPath": "/data"}],
                        },
                    ],
                    "volumes": [{"name": "data", "emptyDir": {}}],
                },
            },
        },
    }

    batch_v1 = k8s_client.BatchV1Api()
    try:
        created = batch_v1.create_namespaced_job(namespace=namespace, body=job_manifest)
    except ApiException as e:
        logger.exception("Failed to create support bundle Job")
        raise HTTPException(
            status_code=500,
            detail=f"Could not start support bundle collection: {e.reason}",
        )

    return {
        "job_name": created.metadata.name,
        "namespace": namespace,
        "status": "started",
        "message": "Support bundle collection started. It will appear in the Vendor Portal in 1-2 minutes.",
    }


@app.get("/budget", response_model=BudgetResponse | None,
         dependencies=[Depends(require_valid_license)])
def get_budget(current_user: Annotated[User, Depends(get_current_user)], db: Session = Depends(get_db)):
    budget = db.query(Budget).filter(Budget.user_id == current_user.id).first()
    return budget


@app.post("/budget", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED,
          dependencies=[Depends(require_valid_license)])
def create_budget(
    budget_data: BudgetCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    existing = db.query(Budget).filter(Budget.user_id == current_user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Budget already exists")
    budget = Budget(user_id=current_user.id, monthly_income=budget_data.monthly_income)
    db.add(budget)
    db.commit()
    db.refresh(budget)
    invalidate_dashboard_cache(current_user.id)
    threading.Thread(target=send_custom_metrics, daemon=True).start()
    return budget


@app.get("/budget/transactions", response_model=list[TransactionResponse],
         dependencies=[Depends(require_valid_license)])
def get_transactions(current_user: Annotated[User, Depends(get_current_user)], db: Session = Depends(get_db)):
    budget = db.query(Budget).filter(Budget.user_id == current_user.id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    return db.query(Transaction).filter(Transaction.budget_id == budget.id).order_by(Transaction.created_at.desc()).all()


@app.post("/budget/transactions", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED,
          dependencies=[Depends(require_valid_license)])
def create_transaction(
    tx_data: TransactionCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    budget = db.query(Budget).filter(Budget.user_id == current_user.id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    # Check license entitlement for custom categories
    if not is_custom_categories_enabled() and tx_data.category not in ("needs", "wants", "savings"):
        raise HTTPException(status_code=400, detail="Category must be needs, wants, or savings. Upgrade to Premium for custom categories.")
    tx = Transaction(
        budget_id=budget.id,
        category=tx_data.category,
        amount=tx_data.amount,
        description=tx_data.description
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    invalidate_dashboard_cache(current_user.id)
    threading.Thread(target=send_custom_metrics, daemon=True).start()
    return tx


@app.delete("/budget/transactions/{tx_id}", dependencies=[Depends(require_valid_license)])
def delete_transaction(
    tx_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    budget = db.query(Budget).filter(Budget.user_id == current_user.id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    tx = db.query(Transaction).filter(Transaction.id == tx_id, Transaction.budget_id == budget.id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    db.delete(tx)
    db.commit()
    invalidate_dashboard_cache(current_user.id)
    threading.Thread(target=send_custom_metrics, daemon=True).start()
    return {"message": "Transaction deleted"}


@app.get("/budget/dashboard", response_model=DashboardData,
         dependencies=[Depends(require_valid_license)])
def get_dashboard(current_user: Annotated[User, Depends(get_current_user)], db: Session = Depends(get_db)):
    # Check Redis cache first
    cached = get_dashboard_cache(current_user.id)
    if cached:
        return DashboardData(**cached)

    budget = db.query(Budget).filter(Budget.user_id == current_user.id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    monthly_income = budget.monthly_income
    if monthly_income <= 0:
        logger.warning(
            "Invalid budget data: monthly income is %.2f for user %d. "
            "This indicates corrupted budget data that bypassed validation.",
            monthly_income, current_user.id
        )
    needs_target = monthly_income * 0.50
    wants_target = monthly_income * 0.30
    savings_target = monthly_income * 0.20

    transactions = db.query(Transaction).filter(Transaction.budget_id == budget.id).all()

    needs_spent = sum(tx.amount for tx in transactions if tx.category == "needs")
    wants_spent = sum(tx.amount for tx in transactions if tx.category == "wants")
    savings_spent = sum(tx.amount for tx in transactions if tx.category == "savings")

    result = DashboardData(
        monthly_income=monthly_income,
        needs_target=needs_target,
        wants_target=wants_target,
        savings_target=savings_target,
        needs_spent=needs_spent,
        wants_spent=wants_spent,
        savings_spent=savings_spent,
        transactions=[
            TransactionResponse(
                id=tx.id,
                budget_id=tx.budget_id,
                category=tx.category,
                amount=tx.amount,
                description=tx.description,
                date=tx.date,
                created_at=tx.created_at
            )
            for tx in sorted(transactions, key=lambda t: t.created_at or t.date, reverse=True)
        ]
    )

    # Cache the computed dashboard for 60 seconds
    set_dashboard_cache(current_user.id, result.model_dump(mode="json"))
    return result
