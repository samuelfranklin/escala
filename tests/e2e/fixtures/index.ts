/**
 * Shared test fixtures for E2E tests.
 *
 * Wraps Playwright's `test` with custom fixtures that provide
 * helpers for common app interactions.
 */
import { test as base, type Page } from '@playwright/test';

/** Navigate to a sidebar route by path */
async function goto(page: Page, path: string): Promise<void> {
  await page.goto(path);
  await page.waitForLoadState('networkidle');
}

/** Close any open modal by pressing Escape */
async function closeModal(page: Page): Promise<void> {
  await page.keyboard.press('Escape');
  await page.waitForTimeout(200);
}

/** Fill a form field by label text */
async function fillField(page: Page, label: string, value: string): Promise<void> {
  const input = page.locator(`label:has-text("${label}") + input, label:has-text("${label}") ~ input`).first();
  await input.clear();
  await input.fill(value);
}

export type AppFixtures = {
  /** Navigates to a page path */
  goto: (path: string) => Promise<void>;
  closeModal: () => Promise<void>;
  fillField: (label: string, value: string) => Promise<void>;
};

export const test = base.extend<AppFixtures>({
  goto: async ({ page }, use) => {
    await use((path: string) => goto(page, path));
  },
  closeModal: async ({ page }, use) => {
    await use(() => closeModal(page));
  },
  fillField: async ({ page }, use) => {
    await use((label: string, value: string) => fillField(page, label, value));
  },
});

export { expect } from '@playwright/test';
