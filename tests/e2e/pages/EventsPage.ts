import type { Page } from '@playwright/test';

export interface EventData {
  name: string;
  date: string; // ISO: 'YYYY-MM-DD'
  type?: 'regular' | 'special' | 'training';
}

export class EventsPage {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  async goto() {
    await this.page.goto('/events');
    await this.page.waitForLoadState('networkidle');
  }

  get rows() {
    return this.page.locator('[data-testid="event-row"]');
  }

  async create(event: EventData) {
    await this.page.locator('[data-testid="btn-new-event"]').click();
    await this.page.waitForSelector('[role="dialog"]', { state: 'visible' });

    await this.page.locator('input[name="name"]').fill(event.name);
    await this.page.locator('input[type="date"]').fill(event.date);

    if (event.type) {
      await this.page.locator('#ev-type').selectOption(event.type);
    }

    await this.page.locator('[data-testid="btn-save-event"]').click();
    await this.page.waitForTimeout(300);
  }

  async rowCount() {
    return this.rows.count();
  }
}
