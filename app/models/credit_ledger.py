"""SQLAlchemy database model for the credit purchase and deduction ledger."""

from __future__ import annotations

import datetime
from sqlalchemy import Column, DateTime, Integer, String
from app.models.base import Base


class CreditTransaction(Base):
    """Credit ledger recording Stripe purchases, package additions, and job usage."""

    __tablename__ = "credit_transactions"

    id = Column(String(128), primary_key=True, index=True)  # Stripe Session ID or txn ID
    user_id = Column(String(128), index=True, nullable=False)
    credits_added = Column(Integer, nullable=False)
    amount_paid_cents = Column(Integer, default=0, nullable=False)
    currency = Column(String(10), default="usd", nullable=False)
    status = Column(String(50), default="completed", nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<CreditTransaction id={self.id} user={self.user_id} credits=+{self.credits_added}>"
