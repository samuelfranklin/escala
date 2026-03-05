import type { Page } from '@playwright/test';

export interface MemberData {
  name: string;
  phone?: string;
  email?: string;
}

export class MembersPage {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  async goto() {
    await this.page.goto('/members');
    await this.page.waitForLoadState('networkidle');
  }

  get rows() {
    return this.page.locator('[data-testid="member-row"]');
  }

  async create(member: MemberData) {
    await this.page.locator('[data-testid="btn-new-member"]').click();
    await this.page.waitForSelector('[role="dialog"]', { state: 'visible' });

    await this.page.locator('input[name="name"]').fill(member.name);
    if (member.phone) {
      await this.page.locator('input[placeholder*="telefone" i], input[placeholder*="99999" i]').fill(member.phone);
    }
    if (member.email) {
      await this.page.locator('input[type="email"]').fill(member.email);
    }

    await this.page.locator('[data-testid="btn-save-member"]').click();
    await this.page.waitForTimeout(300);
  }

  async rowCount() {
    return this.rows.count();
  }
}
