from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class BudgetCreate(BaseModel):
    monthly_income: float

class BudgetResponse(BaseModel):
    id: int
    user_id: int
    monthly_income: float
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TransactionCreate(BaseModel):
    category: str
    amount: float
    description: Optional[str] = None

class TransactionResponse(BaseModel):
    id: int
    budget_id: int
    category: str
    amount: float
    description: Optional[str] = None
    date: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class DashboardData(BaseModel):
    monthly_income: float
    needs_target: float
    wants_target: float
    savings_target: float
    needs_spent: float
    wants_spent: float
    savings_spent: float
    transactions: list[TransactionResponse]
