import { test, expect } from "@playwright/test";

test.describe("Full Application End-to-End User Journey", () => {
  const MOCK_JOB_ID = "job-e2e-journey-full-54321";
  const TEST_REPO_URL = "https://github.com/tiangolo/fastapi";
  const DOWNLOAD_URL = `/api/v1/jobs/${MOCK_JOB_ID}/download`;

  test.beforeEach(async ({ page }) => {
    // -------------------------------------------------------------------------
    // 1. Mock Supabase Authentication Network Handshake
    // -------------------------------------------------------------------------
    await page.route("**/auth/v1/**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          access_token: "mock-supabase-jwt-token-e2e",
          token_type: "bearer",
          expires_in: 3600,
          refresh_token: "mock-supabase-refresh-token",
          user: {
            id: "usr_full_e2e_001",
            email: "creator@studio.com",
            user_metadata: { full_name: "Senior Video Engineer" },
          },
        }),
      });
    });

    // -------------------------------------------------------------------------
    // 2. Mock Billing Endpoints
    // -------------------------------------------------------------------------
    await page.route("**/api/v1/billing/balance", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          credits: 120,
          plan: "Pro Creator",
          cost_per_tutorial_usd: 9.0,
          currency: "USD",
        }),
      });
    });

    await page.route("**/api/v1/billing/add-credits", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          status: "success",
          added_credits: 50,
          new_balance: 170,
          transaction_id: "txn_mock_stripe_checkout_99",
        }),
      });
    });

    // -------------------------------------------------------------------------
    // 3. Mock Video Generation API Handshake
    // -------------------------------------------------------------------------
    await page.route("**/api/v1/generate-video", async (route) => {
      await route.fulfill({
        status: 202,
        contentType: "application/json",
        body: JSON.stringify({
          job_id: MOCK_JOB_ID,
          status: "QUEUED",
          message: "Video tutorial task successfully scheduled in Celery queue.",
        }),
      });
    });

    // Mock initial status poll transitioning to SUCCESS
    await page.route(`**/api/v1/jobs/${MOCK_JOB_ID}`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          job_id: MOCK_JOB_ID,
          status: "SUCCESS",
          progress: 100,
          step: 5,
          step_name: "Completed",
          message: "Tutorial video successfully rendered and assembled!",
          download_url: DOWNLOAD_URL,
          result: {
            duration: 45.5,
            resolution: "1080p",
            theme: "midnight",
            subtitles_burned: true,
          },
        }),
      });
    });

    // Mock SSE real-time stream endpoint
    await page.route(`**/api/v1/jobs/${MOCK_JOB_ID}/stream`, async (route) => {
      await route.fulfill({
        status: 200,
        headers: {
          "Content-Type": "text/event-stream",
          "Cache-Control": "no-cache",
          Connection: "keep-alive",
        },
        body:
          `event: progress\ndata: {"job_id":"${MOCK_JOB_ID}","status":"PROCESSING","progress":75,"step":4,"step_name":"Neural Voice & SRT"}\n\n` +
          `event: complete\ndata: {"job_id":"${MOCK_JOB_ID}","status":"SUCCESS","progress":100,"step":5,"step_name":"Completed","download_url":"${DOWNLOAD_URL}","result":{"duration":45.5}}\n\n`,
      });
    });

    // Mock video stream download endpoint
    await page.route(`**/api/v1/jobs/${MOCK_JOB_ID}/download`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "video/mp4",
        body: Buffer.from("mock-mp4-stream"),
      });
    });
  });

  test("Step 1: Sign up a new user and navigate to dashboard", async ({ page }) => {
    await page.goto("/signup");

    await expect(page.getByRole("heading", { name: /Create your.*account/i })).toBeVisible();

    await page.locator('input[placeholder="Linus Torvalds"]').fill("Alex Johnson");
    await page.locator('input[type="email"]').fill("alex@company.com");
    await page.locator('input[type="password"]').fill("SecurePassword123!");

    const submitBtn = page.getByRole("button", { name: /Create Account/i });
    await expect(submitBtn).toBeEnabled();
    await submitBtn.click();

    // Verify account creation feedback and auto-redirect to dashboard
    await page.waitForURL("**/dashboard", { timeout: 12000 });
    await expect(page).toHaveURL(/.*\/dashboard/);
  });

  test("Step 2-5: Login, check credits, submit repo, monitor progress, and verify video player", async ({
    page,
  }) => {
    // -------------------------------------------------------------------------
    // 1. User Authentication (Login)
    // -------------------------------------------------------------------------
    await page.goto("/login");
    await page.locator('input[type="email"]').fill("creator@studio.com");
    await page.locator('input[type="password"]').fill("SuperSecretKey123!");
    await page.getByRole("button", { name: /Sign In/i }).click();

    await page.waitForURL("**/dashboard", { timeout: 12000 });
    await expect(page).toHaveURL(/.*\/dashboard/);

    // -------------------------------------------------------------------------
    // 2. Dashboard Navigation & Credit Balance Display
    // -------------------------------------------------------------------------
    // Check credit balance pill widget in header
    const creditPill = page.locator("header").getByText(/Credits/i);
    await expect(creditPill).toBeVisible();

    // Check main dashboard title
    await expect(
      page.getByRole("heading", { name: /Codebase to Animated Tutorial/i })
    ).toBeVisible();

    // -------------------------------------------------------------------------
    // 3. Select Sample GitHub Repository
    // -------------------------------------------------------------------------
    // Click quick test sample button for FastAPI Framework
    const sampleBtn = page.getByRole("button", { name: "FastAPI Framework" });
    await expect(sampleBtn).toBeVisible();
    await sampleBtn.click();

    // Verify repository input is populated
    const repoInput = page.locator(
      'input[placeholder*="yamadashy/repomix"], input[placeholder*="github.com"]'
    );
    await expect(repoInput).toHaveValue(TEST_REPO_URL);

    // -------------------------------------------------------------------------
    // 4. Submit Generation Request & Verify Real-Time Progress Tracker
    // -------------------------------------------------------------------------
    const generateBtn = page.getByRole("button", {
      name: /Generate Animated Tutorial/i,
    });
    await expect(generateBtn).toBeEnabled();
    await generateBtn.click();

    // Verify active progress tracking appears
    const jobBadge = page.getByText(`Job: ${MOCK_JOB_ID}`);
    await expect(jobBadge).toBeVisible({ timeout: 10000 });

    // Verify 5-stage pipeline step indicator cards
    await expect(page.getByText("Repomix Ingestion")).toBeVisible();
    await expect(page.getByText("Gemini AI Scripting")).toBeVisible();
    await expect(page.getByText("Manim Animation")).toBeVisible();
    await expect(page.getByText("Neural Voice & SRT")).toBeVisible();
    await expect(page.getByText("FFmpeg Assembly")).toBeVisible();

    // -------------------------------------------------------------------------
    // 5. Validating Video Player Component upon SUCCESS Status
    // -------------------------------------------------------------------------
    // Verify Video Player headline
    const videoHeading = page.getByRole("heading", {
      name: /Animated Video Tutorial/i,
    });
    await expect(videoHeading).toBeVisible({ timeout: 15000 });

    // Verify Source repository attribution
    await expect(page.getByText(`Source: ${TEST_REPO_URL}`)).toBeVisible();

    // Verify Prominent Download MP4 Tutorial Button with exact URL
    const downloadBtn = page.getByRole("link", {
      name: /Download MP4 Tutorial/i,
    });
    await expect(downloadBtn).toBeVisible();
    await expect(downloadBtn).toHaveAttribute("href", DOWNLOAD_URL);

    // Verify HTML5 video element container
    const videoElement = page.locator("video");
    await expect(videoElement).toBeVisible();

    // Verify Share button and New Video reset button
    await expect(page.getByRole("button", { name: "Share" })).toBeVisible();
    await expect(page.getByRole("button", { name: /New Video/i })).toBeVisible();
  });

  test("Step 6: Test Billing Page & Stripe Credit Top-up Modal", async ({
    page,
  }) => {
    // Navigate directly to billing page
    await page.goto("/dashboard/billing");

    // Verify Billing Page Header and Metrics
    await expect(
      page.getByRole("heading", { name: /Credit Balance & Billing/i })
    ).toBeVisible();

    // Verify available balance card
    await expect(page.getByText("Available Balance")).toBeVisible();
    await expect(page.getByText("120").first()).toBeVisible();

    // Open Top-up / Add Credits Modal
    const addCreditsBtn = page.getByRole("button", { name: "Add Credits" });
    await expect(addCreditsBtn).toBeVisible();
    await addCreditsBtn.click();

    // Verify Modal Header
    await expect(
      page.getByRole("heading", { name: "Purchase Rendering Credits" })
    ).toBeVisible();

    // Verify Credit Package Options are visible in modal
    await expect(page.getByText("Starter Pack")).toBeVisible();
    await expect(page.getByText("Pro Creator")).toBeVisible();
    await expect(page.getByText("Studio Scale")).toBeVisible();

    // Submit payment authorization
    const payBtn = page.getByRole("button", {
      name: /Pay \$.*& Add .* Credits/i,
    });
    await expect(payBtn).toBeVisible();
    await payBtn.click();

    // Verify successful payment confirmation screen
    await expect(page.getByText("Payment Approved!")).toBeVisible({
      timeout: 10000,
    });
    await expect(page.getByText(/Added \+.* Credits to your account/i)).toBeVisible();
  });
});
