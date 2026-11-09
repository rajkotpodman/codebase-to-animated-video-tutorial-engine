# 📖 How to Use Codebase-to-Animated Video Tutorial Engine

This comprehensive guide walks you through installing, configuring, running, and generating AI-powered animated architecture tutorial videos from any public GitHub repository.

---

## 📋 Table of Contents
1. [Prerequisites](#1-prerequisites)
2. [Environment Configuration](#2-environment-configuration)
3. [Starting the Application](#3-starting-the-application)
4. [Generating Your First Tutorial Video](#4-generating-your-first-tutorial-video)
5. [Customizing Video Settings](#5-customizing-video-settings)
6. [Purchasing Credits via Binance Pay (1 USDT = 1 Video)](#6-purchasing-credits-via-binance-pay-1-usdt--1-video)
7. [API & Programmatic Generation](#7-api--programmatic-generation)
8. [Troubleshooting & FAQs](#8-troubleshooting--faqs)

---

## 1. Prerequisites

Before running the application locally, ensure you have the following installed:
* **Python**: `3.11` or higher (`python --version`)
* **Node.js**: `18.x` or `20.x` LTS (`node -v` and `npm -v`)
* **FFmpeg**: Must be available on your system PATH (`ffmpeg -version`)
* **Git**: Required to clone public GitHub repositories
* **Google Gemini API Key**: Obtain a free API key at [Google AI Studio](https://aistudio.google.com/)

---

## 2. Environment Configuration

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Open `.env` and set your configuration values:
   ```ini
   # Core AI API Key
   GEMINI_API_KEY=AIzaSy...your_gemini_api_key

   # Server URLs
   BACKEND_API_URL=http://127.0.0.1:8000
   FRONTEND_URL=http://localhost:3000

   # Database (defaults to SQLite for local development)
   DATABASE_URL=sqlite:///./codevideo.db

   # Redis & Celery (optional for local mock mode, required for async task queue)
   REDIS_URL=redis://localhost:6379/0

   # Stripe Billing (Optional)
   STRIPE_SECRET_KEY=sk_test_...
   STRIPE_WEBHOOK_SECRET=whsec_...
   ```

---

## 3. Starting the Application

You can run the engine either using standard local processes or via Docker Compose.

### Option A: Local Development (Recommended for quick testing)

#### 1. Start the FastAPI Backend:
```bash
# In the repository root
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux / macOS:
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
* Backend API is live at `http://127.0.0.1:8000`
* Swagger UI Docs: `http://127.0.0.1:8000/docs`
* Scalar UI Docs: `http://127.0.0.1:8000/scalar`

#### 2. Start the Next.js Frontend:
```bash
# In a new terminal window
cd frontend
npm install
npm run dev
```
* Studio UI is live at `http://localhost:3000`

### Option B: Docker Compose
```bash
docker compose up -d --build
```

---

## 4. Generating Your First Tutorial Video

1. Open your browser and navigate to **`http://localhost:3000/dashboard`**.
2. In the **"Repository URL"** field, paste any public GitHub repository link (e.g. `https://github.com/yamadashy/repomix` or `https://github.com/rajkotpodman/helper-AI`).
3. Select your desired settings:
   - **Resolution**: `1080p Full HD` (1920x1080) or `720p HD` (1280x720)
   - **Language**: English, Hindi, Gujarati, Spanish, French, etc.
   - **Narrator Voice**: Choose from available neural Microsoft voice models.
   - **Visual Theme**: Midnight Dark, Cyberpunk Emerald, Indigo Eclipse.
4. Click **"Generate Architecture Tutorial"**.
5. The live pipeline will process the repository through 6 autonomous stages:
   - `01. Ingestion`: Clones repo and packages structure with Repomix.
   - `02. Graph Analysis`: AST dependency extraction and node topology mapping.
   - `03. Script Synthesis`: Gemini generates multi-scene technical explanation.
   - `04. Neural Audio`: Edge-TTS synthesizes natural spoken voiceover + timestamped subtitles.
   - `05. Manim Animation`: Manim Community renders coordinate-based vector animations.
   - `06. FFmpeg Master`: Syncs frames, applies smart frame freezing (`tpad`), and burns subtitles.
6. Once finished, preview the video directly in the browser player or click **"Download HD MP4"**.

---

## 5. Customizing Video Settings

### Selecting Indian and International Languages
The engine supports 21+ languages natively without external machine translation. Gemini writes the script directly in your requested language, and Edge-TTS reads it with native pronunciation:

* **Hindi (हिन्दी)**: `target_language: "hi"`, voice: `hi-IN-SwaraNeural` or `hi-IN-MadhurNeural`
* **Gujarati (ગુજરાતી)**: `target_language: "gu"`, voice: `gu-IN-NiranjanNeural` or `gu-IN-DhwaniNeural`
* **Marathi (मराठी)**: `target_language: "mr"`, voice: `mr-IN-AarohiNeural`
* **Tamil (தமிழ்)**: `target_language: "ta"`, voice: `ta-IN-PallaviNeural`
* **Spanish (Español)**: `target_language: "es"`, voice: `es-ES-AlvaroNeural`
* **French (Français)**: `target_language: "fr"`, voice: `fr-FR-HenriNeural`

---

## 6. Purchasing Credits via Binance Pay (1 USDT = 1 Video)

We provide a direct, low-cost crypto payment option: **1 Video Tutorial Credit = 1 USDT**.

### How to Pay:
1. Navigate to **`http://localhost:3000/dashboard/billing`**.
2. Click **"Pay 1 USDT (Binance)"** or click **"Add Credits"** and select **Binance (1 USDT)**.
3. Open the **Binance App** on your smartphone.
4. Tap the **Scan (QR)** button in the Binance app and scan the QR code below:

<div align="center">

<a href="https://app.binance.com/uni-qr/5HyzYRA1">
  <img src="docs/images/binance-qr-1usdt.png" alt="Binance Pay 1 USDT QR Code" width="240" style="border-radius: 14px; border: 2px solid #F0B90B;" />
</a>

<br/>

**Direct Link**: [`https://app.binance.com/uni-qr/5HyzYRA1`](https://app.binance.com/uni-qr/5HyzYRA1)

</div>

5. Confirm the transfer of **1 USDT** in your Binance app.
6. **Automatic Deposit**: Our real-time listener detects the payment within 3 seconds, shows a green confirmation animation, and immediately deposits **+1 Video Tutorial Credit** into your account!
7. *(Optional)* You can also tap **"I Have Paid"** in the billing modal to instantly verify your transfer.

---

## 7. API & Programmatic Generation

You can generate videos programmatically via the REST API:

```python
import requests

payload = {
    "repo_url": "https://github.com/rajkotpodman/helper-AI",
    "resolution": "1080p",
    "target_language": "hi",
    "theme": "midnight",
    "focus_notes": "Focus on database routing and async controllers"
}

# 1. Trigger generation job
res = requests.post("http://127.0.0.1:8000/api/v1/generate-video", json=payload)
job_id = res.json()["job_id"]
print(f"Started Job: {job_id}")

# 2. Poll job status
status_res = requests.get(f"http://127.0.0.1:8000/api/v1/jobs/{job_id}")
print("Status:", status_res.json()["status"])
```

---

## 8. Troubleshooting & FAQs

### Q: Why did Next.js show a Hydration Mismatch in dev mode?
* **A:** This happens when a browser extension (such as Urban VPN, Bitwarden, or a translation tool) injects attributes (like `bis_skin_checked="1"`) into the HTML before React loads.
* **Fix**: Open `http://localhost:3000` in an **Incognito / Private Tab** or whitelist `localhost` in your extension settings.

### Q: Does the generated video cut to black at the end?
* **A:** No. Our pipeline incorporates dynamic runtime scaling and an FFmpeg `tpad` filter that freezes the last animated vector card on screen for the full duration of audio voiceovers.

### Q: Where are rendered videos stored?
* **A:** Rendered videos and temporary scene files are saved under `output_artifacts/{job_id}/final_tutorial.mp4` and can be downloaded over HTTP at `/api/v1/jobs/{job_id}/download`.
