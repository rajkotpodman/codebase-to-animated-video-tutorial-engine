"""Database configuration and models for PostgreSQL/SQLite user credits management."""

from __future__ import annotations

import datetime
import logging
import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.models import Base, User, Job, CreditTransaction, BinanceOrder

logger = logging.getLogger("database")

# Environment-configurable Database URL (default to SQLite for local development/testing)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./codevideo.db")

# For PostgreSQL on Heroku or Render with postgres:// prefix
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# SQLite specific connect_args
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Re-export Base, User, Job, and CreditTransaction from app.models for backward compatibility
__all__ = [
    "Base",
    "User",
    "Job",
    "CreditTransaction",
    "BinanceOrder",
    "engine",
    "SessionLocal",
    "get_db",
    "init_db",
    "get_or_create_user",
    "add_user_credits",
    "deduct_user_credit",
]


# -----------------------------------------------------------------------------
# DB Lifecycle and Helpers
# -----------------------------------------------------------------------------


def init_db() -> None:
    """Initialize database tables."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully with URL: %s", DATABASE_URL.split("@")[-1])
    except Exception as exc:
        logger.exception("Failed to initialize database tables: %s", exc)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for obtaining a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_or_create_user(db: Session, user_id: str, email: str, default_credits: int = 120) -> User:
    """Retrieve an existing user or initialize a new record with starting credits."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        # Check by email as secondary check
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.id = user_id
            db.commit()
            db.refresh(user)
            return user

        user = User(
            id=user_id,
            email=email,
            credits=default_credits,
            created_at=datetime.datetime.utcnow(),
            updated_at=datetime.datetime.utcnow(),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info("Created new user in database: %s (Credits: %d)", email, default_credits)
    return user


def add_user_credits(
    db: Session,
    user_id: str,
    credits_to_add: int,
    stripe_session_id: str,
    amount_paid_cents: int,
    currency: str = "usd",
) -> int:
    """Atomically record a Stripe purchase and update the user's credit balance."""
    # Check if this Stripe session was already processed to guarantee idempotency
    existing_txn = db.query(CreditTransaction).filter(CreditTransaction.id == stripe_session_id).first()
    if existing_txn:
        logger.warning("Stripe transaction %s already processed. Skipping duplicate addition.", stripe_session_id)
        user = db.query(User).filter(User.id == user_id).first()
        return user.credits if user else 0

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        user = User(
            id=user_id,
            email=f"{user_id}@example.com",
            credits=credits_to_add,
            created_at=datetime.datetime.utcnow(),
            updated_at=datetime.datetime.utcnow(),
        )
        db.add(user)
    else:
        user.credits += credits_to_add
        user.updated_at = datetime.datetime.utcnow()

    # Record ledger entry
    txn = CreditTransaction(
        id=stripe_session_id,
        user_id=user_id,
        credits_added=credits_to_add,
        amount_paid_cents=amount_paid_cents,
        currency=currency,
        status="completed",
        created_at=datetime.datetime.utcnow(),
    )
    db.add(txn)
    db.commit()
    db.refresh(user)

    logger.info("Successfully added %d credits to user %s. New balance: %d", credits_to_add, user_id, user.credits)
    return user.credits


def deduct_user_credit(db: Session, user_id: str, amount: int = 1) -> bool:
    """Atomically deduct credits from a user's balance. Returns True if successful, False if insufficient credits."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user or user.credits < amount:
        return False
    user.credits -= amount
    user.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(user)
    logger.info("Deducted %d credit(s) from user %s. Remaining: %d", amount, user_id, user.credits)
    return True


# Ensure tables are created upon module import
init_db()
