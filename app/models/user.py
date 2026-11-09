"""SQLAlchemy database model for User accounts and credit balances."""

from __future__ import annotations

import datetime
from sqlalchemy import Column, DateTime, Integer, String
from app.models.base import Base


class User(Base):
    """User account tracking credits and Stripe customer identifiers."""

    __tablename__ = "users"

    id = Column(String(128), primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    credits = Column(Integer, default=120, nullable=False)
    stripe_customer_id = Column(String(128), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} credits={self.credits}>"
