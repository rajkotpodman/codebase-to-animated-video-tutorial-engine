# Type-Safe API Client SDK Generation Guide

This project leverages the open-source **OpenAPI Generator** (`@openapitools/openapi-generator-cli`) to automatically generate strongly-typed client SDKs for **TypeScript** (Next.js frontend & Node.js) and **Python** directly from the FastAPI OpenAPI 3.1 specification.

---

## 🚀 Key Highlights

1. **Zero-Server Extraction:** [`scripts/export_openapi.py`](file:///e:/GitHub%20Codebase-to-Animated%20Video%20Tutorial%20Engine/scripts/export_openapi.py) exports [`openapi.json`](file:///e:/GitHub%20Codebase-to-Animated%20Video%20Tutorial%20Engine/openapi.json) directly from the FastAPI application object without requiring a running server instance.
2. **TypeScript Fetch SDK:** Modern, dependency-free `typescript-fetch` client generated in [`frontend/src/api/`](file:///e:/GitHub%20Codebase-to-Animated%20Video%20Tutorial%20Engine/frontend/src/api) with complete Pydantic model serialization, request/response interfaces, and endpoint classes.
3. **Python Client SDK:** Fully-typed, package-ready Python client generated in [`sdk/python/`](file:///e:/GitHub%20Codebase-to-Animated%20Video%20Tutorial%20Engine/sdk/python) for external developers, microservices, and automated testing.
4. **Convenient Client Wrappers:** Built-in singleton instances in [`frontend/lib/api-client.ts`](file:///e:/GitHub%20Codebase-to-Animated%20Video%20Tutorial%20Engine/frontend/lib/api-client.ts) supporting automatic Supabase JWT Bearer token injection.

---

## 🛠️ Generation Commands

### 1. Unified Python Orchestrator (Cross-Platform)

```bash
# Generate all SDKs (TypeScript + Python)
python scripts/generate_sdk.py --target all

# Generate TypeScript client only
python scripts/generate_sdk.py --target typescript

# Generate Python client only
python scripts/generate_sdk.py --target python
```

### 2. NPM Package Scripts (Inside `frontend/`)

```bash
# Export the latest FastAPI OpenAPI schema to openapi.json
npm run export:schema --prefix frontend

# Generate TypeScript client SDK
npm run generate:api --prefix frontend

# Generate Python client SDK
npm run generate:sdk:python --prefix frontend

# Generate both SDKs in one step
npm run generate:all --prefix frontend
```

---

## 💻 TypeScript SDK Usage (Next.js Frontend)

Import the pre-configured API client or raw generated classes from [`frontend/lib/api-client.ts`](file:///e:/GitHub%20Codebase-to-Animated%20Video%20Tutorial%20Engine/frontend/lib/api-client.ts):

### Triggering Video Generation

```typescript
import { videoApi, GenerateVideoRequest } from "@/lib/api-client";

async function createTutorial() {
  const requestPayload: GenerateVideoRequest = {
    repo_url: "https://github.com/tiangolo/fastapi",
    voice: "en-US-ChristopherNeural",
    resolution: "1080p",
    theme: "midnight",
    burn_subtitles: true,
    run_sync: false,
  };

  const response = await videoApi.generateVideoApiV1GenerateVideoPost({
    generateVideoRequest: requestPayload,
  });

  console.log("Queued Task ID:", response.job_id);
  console.log("Status:", response.status);
}
```

### Querying Job Status

```typescript
import { videoApi } from "@/lib/api-client";

async function checkStatus(jobId: string) {
  const job = await videoApi.getJobStatusApiV1JobsJobIdGet({ jobId });
  console.log(`Progress: ${job.progress}% | Step: ${job.step_name}`);
  if (job.status === "SUCCESS") {
    console.log("Download URL:", job.download_url);
  }
}
```

### Creating Stripe Checkout Sessions

```typescript
import { billingApi, CreateCheckoutSessionRequest } from "@/lib/api-client";

async function purchaseCredits() {
  const session = await billingApi.createCheckoutSessionApiV1BillingCheckoutPost({
    createCheckoutSessionRequest: {
      tier: "starter", // $9 single video generation
    },
  });

  // Redirect user to Stripe Hosted Checkout
  window.location.href = session.checkout_url;
}
```

---

## 🐍 Python SDK Usage (External Client)

Install the generated SDK locally:

```bash
pip install -e sdk/python
```

Execute API calls with full type inference:

```python
import os
from codevideo_client import ApiClient, Configuration
from codevideo_client.api import VideoGenerationPipelineApi
from codevideo_client.models import GenerateVideoRequest

# Configure HTTP client with auth token
config = Configuration(
    host="http://localhost:8000",
    access_token=os.getenv("API_TOKEN"),
)

with ApiClient(config) as api_client:
    api = VideoGenerationPipelineApi(api_client)

    # Submit video generation job
    request = GenerateVideoRequest(
        repo_url="https://github.com/octocat/Hello-World",
        voice="en-US-ChristopherNeural",
        resolution="1080p",
        theme="dark",
    )
    result = api.generate_video_api_v1_generate_video_post(request)
    print(f"Submitted Task ID: {result.job_id}")

    # Query status
    status = api.get_job_status_api_v1_jobs_job_id_get(job_id=result.job_id)
    print(f"Status: {status.status} ({status.progress}%)")
```

---

## ⚙️ Configuration Files

- [`openapitools.json`](file:///e:/GitHub%20Codebase-to-Animated%20Video%20Tutorial%20Engine/openapitools.json): Generator properties and template settings.
- [`scripts/export_openapi.py`](file:///e:/GitHub%20Codebase-to-Animated%20Video%20Tutorial%20Engine/scripts/export_openapi.py): FastAPI schema extractor.
- [`scripts/generate_sdk.py`](file:///e:/GitHub%20Codebase-to-Animated%20Video%20Tutorial%20Engine/scripts/generate_sdk.py): Cross-platform CLI runner.
- [`frontend/lib/api-client.ts`](file:///e:/GitHub%20Codebase-to-Animated%20Video%20Tutorial%20Engine/frontend/lib/api-client.ts): Singleton instances and auth integration.

