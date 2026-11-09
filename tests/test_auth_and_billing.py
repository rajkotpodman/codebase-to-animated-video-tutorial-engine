"""Unit and integration tests for Supabase JWT auth middleware and Stripe billing webhook."""

import datetime
import json
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.auth_middleware import AuthenticatedUser, verify_jwt_token, SUPABASE_JWT_SECRET
from app.core.database import SessionLocal, User, add_user_credits, get_or_create_user
import jwt

client = TestClient(app)


def test_auth_middleware_fallback():
    """Verify auth middleware provides mock developer user when not strictly enforced."""
    res = client.get("/api/v1/billing/balance")
    assert res.status_code == 200
    data = res.json()
    assert "credits" in data
    assert data["cost_per_tutorial_usd"] == 9.0


def test_auth_middleware_jwt_decoding():
    """Verify PyJWT decodes Supabase payload correctly."""
    secret = "test_supabase_jwt_secret_12345_secure_key_32bytes"
    payload = {
        "sub": "user_test_uuid_999",
        "email": "testuser@example.com",
        "role": "authenticated",
        "aud": "authenticated",
        "exp": int(datetime.datetime.utcnow().timestamp()) + 3600,
        "user_metadata": {"full_name": "Test User"},
    }
    token = jwt.encode(payload, secret, algorithm="HS256")

    # In development mode without secret configured, it decodes payload safely
    user = verify_jwt_token(token)
    assert user.user_id == "user_test_uuid_999"
    assert user.email == "testuser@example.com"
    assert user.is_authenticated is True


def test_stripe_checkout_session_creation():
    """Verify Stripe checkout session endpoint handles standard packages ($9 rate)."""
    # 1. Single video tutorial ($9)
    res_single = client.post(
        "/api/v1/billing/create-checkout-session",
        json={"package_id": "single_tutorial"},
    )
    assert res_single.status_code == 200
    data_single = res_single.json()
    assert data_single["credits"] == 1
    assert data_single["amount_usd"] == 9.0
    assert "session_id" in data_single
    assert "checkout_url" in data_single

    # 2. Pro bundle ($399 for 50 credits)
    res_pro = client.post(
        "/api/v1/billing/create-checkout-session",
        json={"package_id": "pro_50"},
    )
    assert res_pro.status_code == 200
    data_pro = res_pro.json()
    assert data_pro["credits"] == 50
    assert data_pro["amount_usd"] == 399.0


def test_stripe_webhook_checkout_completed():
    """Verify Stripe webhook automatically updates user credit balance in PostgreSQL/database."""
    db = SessionLocal()
    test_user_id = f"test_usr_{int(datetime.datetime.utcnow().timestamp())}"
    user = get_or_create_user(db, test_user_id, f"{test_user_id}@example.com", default_credits=10)
    initial_credits = user.credits
    db.close()

    # Simulate Stripe checkout.session.completed event
    session_id = f"cs_test_{int(datetime.datetime.utcnow().timestamp())}"
    webhook_event = {
        "id": f"evt_test_{int(datetime.datetime.utcnow().timestamp())}",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": session_id,
                "client_reference_id": test_user_id,
                "customer_email": f"{test_user_id}@example.com",
                "amount_total": 39900,  # $399.00
                "currency": "usd",
                "metadata": {
                    "user_id": test_user_id,
                    "credits_amount": "50",
                    "package_id": "pro_50",
                },
            }
        },
    }

    # Dispatch webhook POST
    response = client.post(
        "/api/v1/billing/webhook",
        content=json.dumps(webhook_event),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["new_balance"] == initial_credits + 50

    # Test Idempotency: Duplicate delivery of same Stripe session must not double-credit
    dup_response = client.post(
        "/api/v1/billing/webhook",
        content=json.dumps(webhook_event),
        headers={"Content-Type": "application/json"},
    )
    assert dup_response.status_code == 200
    assert dup_response.json()["new_balance"] == initial_credits + 50


def test_binance_pay_order_lifecycle_and_credit_deposit():
    """Verify Binance Pay 1 USDT = 1 Video Credit order creation, polling, and auto-crediting."""
    # 1. Create 1 USDT Binance Pay Order
    res = client.post("/api/v1/billing/binance/create-order", json={"package_id": "binance_1_usdt"})
    assert res.status_code == 200
    data = res.json()
    assert data["amount_usdt"] == 1.0
    assert data["credits"] == 1
    assert data["currency"] == "USDT"
    assert data["status"] == "pending"
    assert data["qr_code_url"] == "/images/binance-qr-1usdt.png"
    assert "https://app.binance.com/uni-qr/" in data["binance_pay_url"]
    order_id = data["order_id"]

    # 2. Check Order Status (pending)
    res_status = client.get(f"/api/v1/billing/binance/order-status/{order_id}")
    assert res_status.status_code == 200
    assert res_status.json()["status"] == "pending"
    assert res_status.json()["is_paid"] is False

    # 3. Confirm Payment (simulating scan / blockchain payment verification)
    res_confirm = client.post(
        "/api/v1/billing/binance/confirm-payment",
        json={"order_id": order_id, "transaction_hash": "tx_test_binance_hash_123"},
    )
    assert res_confirm.status_code == 200
    confirm_data = res_confirm.json()
    assert confirm_data["success"] is True
    assert confirm_data["credits_added"] == 1
    assert confirm_data["status"] == "completed"

    # 4. Check Order Status After Payment (completed / is_paid=True)
    res_status_after = client.get(f"/api/v1/billing/binance/order-status/{order_id}")
    assert res_status_after.status_code == 200
    assert res_status_after.json()["status"] == "completed"
    assert res_status_after.json()["is_paid"] is True

    # 5. Idempotent payment verification (duplicate request must not double credit)
    res_confirm_dup = client.post(
        "/api/v1/billing/binance/confirm-payment",
        json={"order_id": order_id},
    )
    assert res_confirm_dup.status_code == 200
    assert res_confirm_dup.json()["credits_added"] == 0


def test_binance_pay_webhook_fulfillment():
    """Verify official Binance Pay webhook automatically fulfills credits for 1 USDT."""
    # 1. Create order
    res = client.post("/api/v1/billing/binance/create-order", json={"package_id": "binance_1_usdt"})
    order_id = res.json()["order_id"]

    # 2. Simulate Binance Webhook PAY_SUCCESS notification
    webhook_payload = {
        "bizType": "PAY",
        "bizIdStr": "100200300",
        "bizStatus": "PAY_SUCCESS",
        "data": json.dumps({
            "merchantTradeNo": order_id,
            "productType": "Video Tutorial Credits",
            "productName": "1 Video Credit",
            "transactTime": 1711234567,
            "totalFee": "1.00000000",
            "currency": "USDT",
            "transactionId": "TX_BNC_WEBHOOK_TEST",
        }),
    }

    res_hook = client.post("/api/v1/billing/binance/webhook", json=webhook_payload)
    assert res_hook.status_code == 200
    assert res_hook.json()["returnCode"] == "SUCCESS"

    # 3. Status must now reflect completed
    res_status = client.get(f"/api/v1/billing/binance/order-status/{order_id}")
    assert res_status.status_code == 200
    assert res_status.json()["is_paid"] is True
    assert res_status.json()["status"] == "completed"

