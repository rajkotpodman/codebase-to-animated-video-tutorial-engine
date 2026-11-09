"""Integration tests for FastAPI endpoints."""

from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.workers.celery_worker import celery_app

client = TestClient(app)


def test_root_and_health_endpoints():
    res_root = client.get("/")
    assert res_root.status_code == 200
    assert "endpoints" in res_root.json()

    res_health = client.get("/health")
    assert res_health.status_code == 200
    assert res_health.json() == {"status": "healthy"}


def test_languages_endpoint():
    res = client.get("/api/v1/languages")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 20
    # Verify Indian and world languages are in response
    codes = [l["code"] for l in data]
    for expected in ["gu", "hi", "mr", "bn", "ta", "te", "es", "fr", "de", "ja", "en"]:
        assert expected in codes


def test_generate_video_with_target_language():
    from unittest.mock import MagicMock
    from app.api.video_routes import generate_video_pipeline
    mock_task = MagicMock(id="job_mock_gu_123")
    orig_delay = generate_video_pipeline.delay
    try:
        generate_video_pipeline.delay = MagicMock(return_value=mock_task)
        payload = {
            "repo_url": "test/mock-repo",
            "target_language": "gu",
        }
        res = client.post("/api/v1/generate-video", json=payload)
        assert res.status_code == 202
        data = res.json()
        assert data["job_id"] == "job_mock_gu_123"
        assert data["target_language"] == "gu"
        assert "Dhwani" in data["voice"]
    finally:
        generate_video_pipeline.delay = orig_delay


def test_generate_video_async_endpoint():
    # Force Celery eager mode during testing so delays execute in-memory
    celery_app.conf.task_always_eager = True

    payload = {
        "repo_url": "octocat/Hello-World",
        "voice": "en-US-ChristopherNeural",
        "resolution": "480p",
        "theme": "midnight",
        "burn_subtitles": True,
    }

    response = client.post("/api/v1/generate-video", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert "job_id" in data
    assert data["status"] in ("QUEUED", "COMPLETED")
    assert "/api/v1/jobs/" in data["status_url"]


def test_get_job_status_endpoint():
    # Query a non-existent or dummy pending job
    res = client.get("/api/v1/jobs/dummy-job-12345")
    assert res.status_code == 200
    data = res.json()
    assert data["job_id"] == "dummy-job-12345"
    assert "status" in data


def test_billing_endpoints():
    # Test balance endpoint
    res_bal = client.get("/api/v1/billing/balance")
    assert res_bal.status_code == 200
    bal_data = res_bal.json()
    assert "credits" in bal_data
    assert bal_data["cost_per_tutorial_usd"] == 9.0

    # Test history endpoint
    res_hist = client.get("/api/v1/billing/history")
    assert res_hist.status_code == 200
    hist_data = res_hist.json()
    assert isinstance(hist_data, list)
    assert len(hist_data) >= 1
    assert "repo_name" in hist_data[0]
    assert "cost_usd" in hist_data[0]

    # Test add credits endpoint
    add_payload = {
        "package_id": "tier_50",
        "credits_to_add": 50,
        "amount_usd": 45.00,
        "payment_method": "card_mock_visa",
    }
    res_add = client.post("/api/v1/billing/add-credits", json=add_payload)
    assert res_add.status_code == 200
    add_data = res_add.json()
    assert add_data["success"] is True
    assert add_data["credits_added"] == 50
    assert add_data["new_balance"] >= bal_data["credits"] + 50
