# 🔌 REST API & WebSocket Reference

The Codebase-to-Animated Video Tutorial Engine exposes interactive OpenAPI specifications via:
* **Swagger UI**: `http://localhost:8000/docs`
* **Scalar API Reference**: `http://localhost:8000/scalar`
* **ReDoc**: `http://localhost:8000/redoc`

---

## 1. Video Generation Endpoints

### `POST /api/v1/generate-video`
Triggers the asynchronous 6-stage video tutorial generation pipeline.

**Request Body:**
```json
{
  "repo_url": "https://github.com/rajkotpodman/helper-AI",
  "resolution": "1080p",
  "target_language": "hi",
  "theme": "midnight",
  "focus_notes": "Emphasize architectural controllers and database models"
}
```

**Response (200 OK):**
```json
{
  "job_id": "job_local_a928cfcd7d",
  "status": "QUEUED",
  "estimated_duration_seconds": 90,
  "stream_url": "/api/v1/jobs/job_local_a928cfcd7d/stream",
  "download_url": "/api/v1/jobs/job_local_a928cfcd7d/download"
}
```

---

### `GET /api/v1/jobs/{job_id}`
Returns current job status, execution stage, and progress percentage.

**Response (200 OK):**
```json
{
  "job_id": "job_local_a928cfcd7d",
  "status": "COMPLETED",
  "progress": 100,
  "stage": "Video Composition & Subtitle Sync",
  "video_url": "/api/v1/jobs/job_local_a928cfcd7d/download",
  "duration_seconds": 173.03,
  "resolution": "1080p"
}
```

---

### `GET /api/v1/jobs/{job_id}/stream`
Server-Sent Events (SSE) stream for real-time progress bars and log streams.

**Event Format:**
```text
event: progress
data: {"job_id": "job_local_a928cfcd7d", "stage": "Manim Animation Rendering", "progress": 75}
```

---

### `GET /api/v1/jobs/{job_id}/download`
Streams the rendered broadcast-quality H.264 MP4 video tutorial file with HTTP Range support for browser seeking.

---

### `GET /api/v1/languages`
Lists all 21+ supported multilingual voiceover configurations, language codes, and Microsoft Neural TTS voice names.

---

## 2. Binance Pay Crypto Endpoints (1 USDT = 1 Video)

### `POST /api/v1/billing/binance/create-order`
Creates a Binance Pay order for purchasing video tutorial credits.

**Request Body:**
```json
{
  "package_id": "binance_1_usdt",
  "credits": 1,
  "amount_usdt": 1.0
}
```

**Response (200 OK):**
```json
{
  "order_id": "BNC_ORD_2C44CA11D861",
  "package_id": "binance_1_usdt",
  "credits": 1,
  "amount_usdt": 1.0,
  "currency": "USDT",
  "status": "pending",
  "qr_code_url": "/images/binance-qr-1usdt.png",
  "binance_pay_url": "https://app.binance.com/uni-qr/5HyzYRA1",
  "created_at": "2026-11-09T05:00:00Z",
  "expires_at": "2026-11-09T05:30:00Z",
  "instructions": "Scan the QR code with the Binance App or tap 'Open in Binance' to pay 1 USDT."
}
```

---

### `GET /api/v1/billing/binance/order-status/{order_id}`
Real-time polling endpoint used by frontend modals to auto-detect payment completion.

**Response (200 OK):**
```json
{
  "order_id": "BNC_ORD_2C44CA11D861",
  "status": "completed",
  "credits": 1,
  "amount_usdt": 1.0,
  "is_paid": true,
  "new_balance": 575,
  "completed_at": "2026-11-09T05:01:15Z"
}
```

---

### `POST /api/v1/billing/binance/confirm-payment`
Instant manual verification endpoint for confirming completed transfers.

**Request Body:**
```json
{
  "order_id": "BNC_ORD_2C44CA11D861",
  "transaction_hash": "tx_binance_blockchain_hash_123"
}
```

---

### `POST /api/v1/billing/binance/webhook`
Official Binance Pay asynchronous webhook listener handling `bizStatus == "PAY_SUCCESS"`.

---

## 3. Stripe & Balance Endpoints

* `GET /api/v1/billing/balance`: Returns the authenticated user's current video credits balance.
* `POST /api/v1/billing/create-checkout-session`: Generates Stripe hosted checkout URLs for standard fiat subscriptions ($9 per video).
* `POST /api/v1/billing/webhook`: Official Stripe Webhook listener for `checkout.session.completed` events.
