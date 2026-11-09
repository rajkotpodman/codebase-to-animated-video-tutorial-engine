import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright E2E configuration for Next.js CodeVideo AI frontend.
 * See https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  testDir: "./e2e",
  /* Maximum time one test can run for */
  timeout: 45 * 1000,
  expect: {
    timeout: 10 * 1000,
  },
  /* Run tests sequentially or in parallel */
  fullyParallel: true,
  /* Fail build on CI if test.only is left */
  forbidOnly: !!process.env.CI,
  /* Retry on failure in CI */
  retries: process.env.CI ? 2 : 0,
  /* Reporter to use */
  reporter: process.env.CI ? [["list"], ["junit", { outputFile: "test-results/results.xml" }]] : "list",
  /* Shared settings for test projects */
  use: {
    baseURL: process.env.PLAYWRIGHT_TEST_BASE_URL || "http://localhost:3000",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  /* Automatically start Next.js web server if not already running */
  webServer: {
    command: "npm run dev",
    url: "http://localhost:3000",
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000,
  },
});
