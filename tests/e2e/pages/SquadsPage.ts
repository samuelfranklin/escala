import type { Page } from '@playwright/test';

export interface SquadData {
  name: string;
  description?: string;
}

export class SquadsPage {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  async goto() {
    await this.page.goto('/squads');
    await this.page.waitForLoadState('networkidle');
  }

  get rows() {
    return this.page.locator('[data-testid="squad-row"]');
  }

  async create(squad: SquadData) {
    await this.page.locator('[data-testid="btn-new-squad"]').click();
    await this.page.waitForSelector('[role="dialog"]', { state: 'visible' });

    await this.page.locator('input[name="name"]').fill(squad.name);

    await this.page.locator('[data-testid="btn-save-squad"]').click();
    await this.page.waitForTimeout(300);
  }

  async selectByName(name: string) {
    await this.page.locator(`[data-testid="squad-row"]:has-text("${name}")`).click();
    await this.page.waitForTimeout(400);
  }

  async addMember(memberName: string) {
    await this.page.locator('[data-testid="select-add-member"]').selectOption({ label: memberName });
    await this.page.locator('[data-testid="btn-add-member"]').click();
    await this.page.waitForTimeout(300);
  }

  async rowCount() {
    return this.rows.count();
  }
}
