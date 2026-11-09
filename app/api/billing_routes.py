"""FastAPI billing and credit management endpoints."""

from __future__ import annotations

import datetime
import logging
from typing import List
from pydantic import BaseModel, Field
from fastapi import APIRouter

logger = logging.getLogger("api_billing_routes")

router = APIRouter(prefix="/api/v1/billing", tags=["Billing & Credits"])

# In-memory mock credit balance and transaction history
_USER_BILLING_STATE = {
    "credits": 120,
    "plan": "Pro Creator",
    "cost_per_tutorial_usd": 9.0,
    "currency": "USD",
}

_MOCK_JOB_HISTORY = [
    {
        "id": "job_repomix_01",
        "job_id": "6a3e218f-9a74-4b5d-8d4e-128a123f001a",
        "repo_name": "yamadashy/repomix",
        "timestamp": (
            datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=2, minutes=15)
        ).isoformat(),
        "duration_seconds": 45,
        "resolution": "1080p",
        "cost_credits": 1,
        "cost_usd": 9.00,
        "status": "COMPLETED",
    },
    {
        "id": "job_fastapi_02",
        "job_id": "8f12c90a-1123-4567-89ab-cdef01234567",
        "repo_name": "tiangolo/fastapi",
        "timestamp": (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1, hours=4)).isoformat(),
        "duration_seconds": 72,
        "resolution": "1080p",
        "cost_credits": 1,
        "cost_usd": 9.00,
        "status": "COMPLETED",
    },
    {
        "id": "job_manim_03",
        "job_id": "3b4c5d6e-7f8a-9b0c-1d2e-3f4a5b6c7d8e",
        "repo_name": "ManimCommunity/manim",
        "timestamp": (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=3, hours=10)).isoformat(),
        "duration_seconds": 58,
        "resolution": "720p",
        "cost_credits": 1,
        "cost_usd": 9.00,
        "status": "COMPLETED",
    },
    {
        "id": "job_octocat_04",
        "job_id": "99aa88bb-77cc-66dd-55ee-44ff33aa22bb",
        "repo_name": "octocat/Hello-World",
        "timestamp": (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=6, hours=1)).isoformat(),
        "duration_seconds": 28,
        "resolution": "1080p",
        "cost_credits": 1,
        "cost_usd": 9.00,
        "status": "COMPLETED",
    },
]


# -----------------------------------------------------------------------------
# Schemas
# -----------------------------------------------------------------------------


class BalanceResponse(BaseModel):
    credits: int
    plan: str
    cost_per_tutorial_usd: float
    currency: str


class JobBillingItem(BaseModel):
    id: str
    job_id: str
    repo_name: str
    timestamp: str
    duration_seconds: int
    resolution: str
    cost_credits: int
    cost_usd: float
    status: str


class AddCreditsRequest(BaseModel):
    package_id: str = Field(default="tier_50", description="Selected credit package identifier")
    credits_to_add: int = Field(default=50, ge=5, le=500, description="Number of credits purchased")
    amount_usd: float = Field(default=45.00, ge=1.0, description="Amount charged in USD")
    payment_method: str = Field(default="card_mock_visa_4242", description="Payment method token")


class AddCreditsResponse(BaseModel):
    success: bool
    transaction_id: str
    previous_balance: int
    new_balance: int
    credits_added: int
    amount_paid_usd: float
    receipt_url: str
    message: str


# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------


@router.get("/balance", response_model=BalanceResponse, summary="Get current user credit balance")
async def get_balance():
    """Retrieve the user's available video generation credits and pricing."""
    return BalanceResponse(
        credits=_USER_BILLING_STATE["credits"],
        plan=_USER_BILLING_STATE["plan"],
        cost_per_tutorial_usd=_USER_BILLING_STATE["cost_per_tutorial_usd"],
        currency=_USER_BILLING_STATE["currency"],
    )


@router.get("/history", response_model=List[JobBillingItem], summary="List past video generation billing history")
async def get_billing_history():
    """List historical video generation jobs, duration, timestamp, and credit deductions."""
    return _MOCK_JOB_HISTORY


@router.post("/add-credits", response_model=AddCreditsResponse, summary="Simulate credit purchase payment")
async def add_credits(payload: AddCreditsRequest):
    """Process a mock credit top-up and update the active balance."""
    prev = _USER_BILLING_STATE["credits"]
    _USER_BILLING_STATE["credits"] += payload.credits_to_add

    txn_id = f"txn_mock_{int(datetime.datetime.now(datetime.timezone.utc).timestamp())}"

    return AddCreditsResponse(
        success=True,
        transaction_id=txn_id,
        previous_balance=prev,
        new_balance=_USER_BILLING_STATE["credits"],
        credits_added=payload.credits_to_add,
        amount_paid_usd=payload.amount_usd,
        receipt_url=f"/api/v1/billing/receipts/{txn_id}",
        message=f"Successfully added {payload.credits_to_add} credits! New balance is {_USER_BILLING_STATE['credits']}.",
    )
