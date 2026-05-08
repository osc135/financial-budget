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

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Financial Budget API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Financial Budget API"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
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
    return new_user

@app.post("/auth/login")
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": str(user.id)}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer", "user": {"id": user.id, "username": user.username}}

@app.get("/budget", response_model=BudgetResponse | None)
def get_budget(current_user: Annotated[User, Depends(get_current_user)], db: Session = Depends(get_db)):
    budget = db.query(Budget).filter(Budget.user_id == current_user.id).first()
    return budget

@app.post("/budget", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
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
    return budget

@app.get("/budget/transactions", response_model=list[TransactionResponse])
def get_transactions(current_user: Annotated[User, Depends(get_current_user)], db: Session = Depends(get_db)):
    budget = db.query(Budget).filter(Budget.user_id == current_user.id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    return db.query(Transaction).filter(Transaction.budget_id == budget.id).order_by(Transaction.created_at.desc()).all()

@app.post("/budget/transactions", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    tx_data: TransactionCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    budget = db.query(Budget).filter(Budget.user_id == current_user.id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    if tx_data.category not in ("needs", "wants", "savings"):
        raise HTTPException(status_code=400, detail="Category must be needs, wants, or savings")
    tx = Transaction(
        budget_id=budget.id,
        category=tx_data.category,
        amount=tx_data.amount,
        description=tx_data.description
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx

@app.delete("/budget/transactions/{tx_id}")
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
    return {"message": "Transaction deleted"}

@app.get("/budget/dashboard", response_model=DashboardData)
def get_dashboard(current_user: Annotated[User, Depends(get_current_user)], db: Session = Depends(get_db)):
    budget = db.query(Budget).filter(Budget.user_id == current_user.id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    
    monthly_income = budget.monthly_income
    needs_target = monthly_income * 0.50
    wants_target = monthly_income * 0.30
    savings_target = monthly_income * 0.20
    
    transactions = db.query(Transaction).filter(Transaction.budget_id == budget.id).all()
    
    needs_spent = sum(tx.amount for tx in transactions if tx.category == "needs")
    wants_spent = sum(tx.amount for tx in transactions if tx.category == "wants")
    savings_spent = sum(tx.amount for tx in transactions if tx.category == "savings")
    
    return DashboardData(
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
