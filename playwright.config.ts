import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright E2E configuration for Tauri.
 *
 * Tauri exposes the webview via WebDriver. For CI/local runs we launch
 * the app via `tauri dev` and Playwright connects to it through the
 * tauri-driver bridge (https://crates.io/crates/tauri-driver).
 *
 * Local usage:
 *   npx playwright test                 # runs all tests
 *   npx playwright test --ui            # opens Playwright UI mode
 */
export default defineConfig({
  testDir: './tests/e2e',
  timeout: 60_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,         // desktop app tests must run sequentially
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,                   // one browser window at a time
  reporter: [
    ['list'],
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
  ],

  use: {
    // Tauri localhost dev server
    baseURL: 'http://localhost:1420',
    // Keep context alive between tests in the same file (app state)
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  // Start `tauri dev` before running tests (local only; CI uses pre-built binary)
  webServer: process.env.CI
    ? undefined
    : {
        command: 'npm run tauri dev -- --no-watch',
        url: 'http://localhost:1420',
        reuseExistingServer: !process.env.CI,
        timeout: 120_000,
      },
});
