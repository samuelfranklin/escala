import type { Page } from '@playwright/test';

export class SchedulePage {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  async goto() {
    await this.page.goto('/schedule');
    await this.page.waitForLoadState('networkidle');
  }

  get container() {
    return this.page.locator('[data-testid="schedule-page"]');
  }

  get pivotTable() {
    return this.page.locator('table');
  }

  async selectEvent(index: number) {
    await this.page.locator('#event-select').selectOption({ index });
    await this.page.waitForTimeout(500);
  }

  async generate() {
    await this.page.locator('[data-testid="btn-generate-schedule"]').click();
    await this.page.waitForTimeout(1500);
  }

  async copy() {
    await this.page.locator('[data-testid="btn-copy-schedule"]').click();
  }

  async exportCsv() {
    await this.page.locator('[data-testid="btn-export-csv"]').click();
  }
}
