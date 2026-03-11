/**
 * Shared test fixtures — expõe Page Objects para todos os testes E2E.
 */
import { test as base } from '@playwright/test';
import { MembersPage } from '../pages/MembersPage';
import { SquadsPage }  from '../pages/SquadsPage';
import { EventsPage }  from '../pages/EventsPage';
import { SchedulePage } from '../pages/SchedulePage';
import { DashboardPage } from '../pages/DashboardPage';

export type AppFixtures = {
  membersPage: MembersPage;
  squadsPage: SquadsPage;
  eventsPage: EventsPage;
  schedulePage: SchedulePage;
  dashboardPage: DashboardPage;
};

export const test = base.extend<AppFixtures>({
  membersPage:  async ({ page }, use) => use(new MembersPage(page)),
  squadsPage:   async ({ page }, use) => use(new SquadsPage(page)),
  eventsPage:   async ({ page }, use) => use(new EventsPage(page)),
  schedulePage: async ({ page }, use) => use(new SchedulePage(page)),
  dashboardPage: async ({ page }, use) => use(new DashboardPage(page)),
});

export { expect } from '@playwright/test';

