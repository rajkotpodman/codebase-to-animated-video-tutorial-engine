import { test, expect } from "@playwright/test";

test.describe("Video Tutorial Generation E2E Workflow", () => {
  const MOCK_JOB_ID = "job-e2e-playwright-98765";
  const TEST_REPO_URL = "https://github.com/octocat/Hello-World";

  test.beforeEach(async ({ page }) => {
    // -------------------------------------------------------------------------
    // 1. Mock Supabase Auth Endpoint
    // -------------------------------------------------------------------------
    await page.route("**/auth/v1/**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          access_token: "mock-jwt-token-playwright",
          token_type: "bearer",
          expires_in: 3600,
          refresh_token: "mock-refresh-token",
          user: {
            id: "user_e2e_12345",
            email: "developer@company.com",
            user_metadata: { full_name: "Test Developer" },
          },
        }),
      });
    });

    // -------------------------------------------------------------------------
    // 2. Mock Backend POST /api/v1/generate-video
    // -------------------------------------------------------------------------
    await page.route("**/api/v1/generate-video", async (route) => {
      const requestData = JSON.parse(route.request().postData() || "{}");
      expect(requestData.repo_url).toBe(TEST_REPO_URL);

      await route.fulfill({
        status: 202,
        contentType: "application/json",
        body: JSON.stringify({
          job_id: MOCK_JOB_ID,
          status: "QUEUED",
          message: "Video generation task queued successfully.",
        }),
      });
    });

    // -------------------------------------------------------------------------
    // 3. Mock Backend GET /api/v1/jobs/{job_id} status poll
    // -------------------------------------------------------------------------
    await page.route(`**/api/v1/jobs/${MOCK_JOB_ID}`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          job_id: MOCK_JOB_ID,
          status: "PROCESSING",
          progress: 40,
          step: 2,
          step_name: "Gemini AI Scripting",
          message: "Synthesizing architectural scenes and voiceover narration...",
        }),
      });
    });

    // -------------------------------------------------------------------------
    // 4. Mock Backend SSE stream route (keep-alive stream fallback)
    // -------------------------------------------------------------------------
    await page.route(`**/api/v1/jobs/${MOCK_JOB_ID}/stream`, async (route) => {
      await route.fulfill({
        status: 200,
        headers: {
          "Content-Type": "text/event-stream",
          "Cache-Control": "no-cache",
          Connection: "keep-alive",
        },
        body: `event: progress\ndata: {"job_id":"${MOCK_JOB_ID}","status":"PROCESSING","progress":40,"step":2,"step_name":"Gemini AI Scripting","message":"Synthesizing architectural scenes"}\n\n`,
      });
    });
  });

  test("full end-to-end user flow: login -> input repo -> submit -> verify progress tracker", async ({
    page,
  }) => {
    // -------------------------------------------------------------------------
    // Step 1: User Login
    // -------------------------------------------------------------------------
    await page.goto("/login");

    // Assert login page header is visible
    await expect(page.getByRole("heading", { name: "Welcome back" })).toBeVisible();

    // Fill in authentication credentials
    const emailInput = page.locator('input[type="email"]');
    const passwordInput = page.locator('input[type="password"]');

    await emailInput.fill("developer@company.com");
    await passwordInput.fill("SuperSecretPassword123!");

    // Submit login form
    const signInButton = page.getByRole("button", { name: /Sign In/i });
    await expect(signInButton).toBeEnabled();
    await signInButton.click();

    // Verify successful redirection to Dashboard
    await page.waitForURL("**/dashboard", { timeout: 10000 });
    await expect(page).toHaveURL(/.*\/dashboard/);
    await expect(
      page.getByRole("heading", { name: /Codebase to Animated Tutorial/i })
    ).toBeVisible();

    // -------------------------------------------------------------------------
    // Step 2: Enter GitHub Repository URL in Video Generation Form
    // -------------------------------------------------------------------------
    const repoInput = page.locator(
      'input[placeholder*="yamadashy/repomix"], input[placeholder*="github.com"]'
    );
    await expect(repoInput).toBeVisible();
    await repoInput.fill(TEST_REPO_URL);

    // Verify value was entered accurately
    await expect(repoInput).toHaveValue(TEST_REPO_URL);

    // -------------------------------------------------------------------------
    // Step 3: Submit the Video Generation Request
    // -------------------------------------------------------------------------
    const submitButton = page.getByRole("button", {
      name: /Generate Animated Tutorial/i,
    });
    await expect(submitButton).toBeEnabled();
    await submitButton.click();

    // -------------------------------------------------------------------------
    // Step 4: Verify the Progress Tracker Component
    // -------------------------------------------------------------------------
    // Verify Job ID is visible in the progress tracker
    const jobBadge = page.getByText(`Job: ${MOCK_JOB_ID}`);
    await expect(jobBadge).toBeVisible({ timeout: 10000 });

    // Verify Pipeline Progress headline or status indicator is displayed
    const progressHeadline = page.getByRole("heading", {
      name: /Rendering Animated Tutorial|Video Task Queued|Tutorial Video Generation/i,
    });
    await expect(progressHeadline).toBeVisible();

    // Verify the 5-stage pipeline steps are rendered
    await expect(page.getByText("Repomix Ingestion")).toBeVisible();
    await expect(page.getByText("Gemini AI Scripting")).toBeVisible();
    await expect(page.getByText("Manim Animation")).toBeVisible();
  });

  test("form validation error displayed when invalid GitHub URL is submitted", async ({
    page,
  }) => {
    await page.goto("/dashboard");

    const repoInput = page.locator(
      'input[placeholder*="yamadashy/repomix"], input[placeholder*="github.com"]'
    );
    await repoInput.fill("invalid-non-github-url");

    const submitButton = page.getByRole("button", {
      name: /Generate Animated Tutorial/i,
    });
    await submitButton.click();

    // Verify validation alert is shown
    await expect(
      page.getByText(/Please enter a valid GitHub repository URL/i)
    ).toBeVisible();
  });
});

