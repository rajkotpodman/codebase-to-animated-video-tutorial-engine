"""SQLAlchemy database model for Binance Pay crypto orders."""

from __future__ import annotations

import datetime
from sqlalchemy import Column, DateTime, Float, Integer, String
from app.models.base import Base


class BinanceOrder(Base):
    """Tracks Binance Pay orders for 1 USDT = 1 Video Credit deposits."""

    __tablename__ = "binance_orders"

    id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(128), index=True, nullable=False)
    package_id = Column(String(64), default="binance_1_usdt", nullable=False)
    credits = Column(Integer, default=1, nullable=False)
    amount_usdt = Column(Float, default=1.0, nullable=False)
    currency = Column(String(10), default="USDT", nullable=False)
    status = Column(String(32), default="pending", index=True, nullable=False)
    qr_code_url = Column(String(256), default="/images/binance-qr-1usdt.png", nullable=False)
    binance_pay_url = Column(String(256), default="https://app.binance.com/uni-qr/5HyzYRA1", nullable=False)
    transaction_hash = Column(String(256), nullable=True)
    payer_binance_id = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<BinanceOrder id={self.id} user={self.user_id} amount={self.amount_usdt} status={self.status}>"

