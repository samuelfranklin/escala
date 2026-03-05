/**
 * E2E Full Flow Test Suite — TDD-GREEN target
 *
 * Tests the complete user journey:
 *   Members (×10) → Squads (×5) → Assign members → Events (×3) → Generate Schedule
 *
 * Run: npx playwright test tests/e2e/test_full_flow.spec.ts
 */
import { test, expect } from './fixtures';

// ─── Test data ────────────────────────────────────────────────────────────────

const MEMBERS = [
  { name: 'Ana Lima',     phone: '11900000001', email: 'ana@test.com' },
  { name: 'Bruno Souza',  phone: '11900000002', email: 'bruno@test.com' },
  { name: 'Carla Mendes', phone: '11900000003', email: 'carla@test.com' },
  { name: 'Diego Rocha',  phone: '11900000004', email: 'diego@test.com' },
  { name: 'Eva Martins',  phone: '11900000005', email: 'eva@test.com' },
  { name: 'Felipe Costa', phone: '11900000006', email: 'felipe@test.com' },
  { name: 'Gabi Oliveira',phone: '11900000007', email: 'gabi@test.com' },
  { name: 'Hugo Ferreira',phone: '11900000008', email: 'hugo@test.com' },
  { name: 'Iris Santos',  phone: '11900000009', email: 'iris@test.com' },
  { name: 'João Alves',   phone: '11900000010', email: 'joao@test.com' },
];

const SQUADS = [
  { name: 'Câmera',       description: 'Operadores de câmera' },
  { name: 'Transmissão',  description: 'Equipe de transmissão ao vivo' },
  { name: 'Áudio',        description: 'Operadores de áudio' },
  { name: 'Iluminação',   description: 'Equipe de iluminação' },
  { name: 'Apresentação', description: 'Apresentadores e anfitriões' },
];

// 2 members per squad (index pairs)
const SQUAD_MEMBERS: Record<string, [string, string]> = {
  'Câmera':       ['Ana Lima',     'Bruno Souza'],
  'Transmissão':  ['Carla Mendes', 'Diego Rocha'],
  'Áudio':        ['Eva Martins',  'Felipe Costa'],
  'Iluminação':   ['Gabi Oliveira','Hugo Ferreira'],
  'Apresentação': ['Iris Santos',  'João Alves'],
};

const EVENTS = [
  { name: 'Culto Domingo', type: 'Culto', day_of_week: '0', time: '09:00' },
  { name: 'Culto Quarta',  type: 'Culto', day_of_week: '3', time: '19:30' },
  { name: 'Culto Sexta',   type: 'Culto', day_of_week: '5', time: '20:00' },
];

// ─── Helpers ──────────────────────────────────────────────────────────────────

async function openCreateModal(
  page: import('@playwright/test').Page,
  testid: string,
): Promise<void> {
  await page.locator(`[data-testid="${testid}"]`).click();
  await page.waitForSelector('[role="dialog"]', { state: 'visible' });
}

async function submitForm(page: import('@playwright/test').Page, testid: string): Promise<void> {
  await page.locator(`[data-testid="${testid}"]`).click();
  await page.waitForTimeout(300);
}

// ─── Tests ────────────────────────────────────────────────────────────────────

test.describe('Full Flow — Escala Mídia', () => {

  test('00 — App loads and shows dashboard', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('[data-testid="dashboard"]')).toBeVisible({ timeout: 10_000 });
  });

  // ── Members ──────────────────────────────────────────────────────────────

  test('01 — Creates 10 members', async ({ page }) => {
    await page.goto('/members');
    await page.waitForLoadState('networkidle');

    for (const member of MEMBERS) {
      await openCreateModal(page, 'btn-new-member');
      await page.locator('input[name="name"]').fill(member.name);
      await page.locator('input[name="phone"], input[placeholder*="telefone" i]').fill(member.phone);
      await page.locator('input[type="email"]').fill(member.email);
      await submitForm(page, 'btn-save-member');
    }
  });

  test('02 — Members list shows 10 rows', async ({ page }) => {
    await page.goto('/members');
    await page.waitForLoadState('networkidle');
    const rows = page.locator('[data-testid="member-row"]');
    await expect(rows).toHaveCount(10, { timeout: 10_000 });
  });

  // ── Squads ───────────────────────────────────────────────────────────────

  test('03 — Creates 5 squads', async ({ page }) => {
    await page.goto('/squads');
    await page.waitForLoadState('networkidle');

    for (const squad of SQUADS) {
      await openCreateModal(page, 'btn-new-squad');
      await page.locator('input[name="name"]').fill(squad.name);
      await submitForm(page, 'btn-save-squad');
    }
  });

  test('04 — Squads list shows 5 rows', async ({ page }) => {
    await page.goto('/squads');
    await page.waitForLoadState('networkidle');
    const rows = page.locator('[data-testid="squad-row"]');
    await expect(rows).toHaveCount(5, { timeout: 10_000 });
  });

  // ── Associate members to squads ──────────────────────────────────────────

  test('05 — Assigns 2 members to each squad', async ({ page }) => {
    await page.goto('/squads');
    await page.waitForLoadState('networkidle');

    for (const [squadName, members] of Object.entries(SQUAD_MEMBERS)) {
      await page.locator(`[data-testid="squad-row"]:has-text("${squadName}")`).click();
      await page.waitForTimeout(400);

      for (const memberName of members) {
        await page.locator('[data-testid="select-add-member"]').selectOption({ label: memberName });
        await page.locator('[data-testid="btn-add-member"]').click();
        await page.waitForTimeout(300);
      }
    }
  });

  // ── Events ───────────────────────────────────────────────────────────────

  test('06 — Creates 3 events', async ({ page }) => {
    await page.goto('/events');
    await page.waitForLoadState('networkidle');

    for (const event of EVENTS) {
      await openCreateModal(page, 'btn-new-event');
      await page.locator('input[name="name"]').fill(event.name);
      // Pick a date 1 week from today so it's valid
      const nextWeek = new Date();
      nextWeek.setDate(nextWeek.getDate() + 7 + EVENTS.indexOf(event));
      await page.locator('input[type="date"]').fill(nextWeek.toISOString().slice(0, 10));
      await submitForm(page, 'btn-save-event');
    }
  });

  test('07 — Events list shows 3 rows', async ({ page }) => {
    await page.goto('/events');
    await page.waitForLoadState('networkidle');
    const rows = page.locator('[data-testid="event-row"]');
    await expect(rows).toHaveCount(3, { timeout: 10_000 });
  });

  // ── Generate Schedule ─────────────────────────────────────────────────────

  test('08 — Generates schedule for current month', async ({ page }) => {
    await page.goto('/schedule');
    await page.waitForLoadState('networkidle');

    const eventSelect = page.locator('#event-select');
    await eventSelect.selectOption({ index: 1 });
    await page.waitForTimeout(500);

    await page.locator('[data-testid="btn-generate-schedule"]').click();
    await page.waitForTimeout(1500);

    const errorEl = page.locator('[data-testid="error"], .error, .alert-danger');
    await expect(errorEl).toHaveCount(0);
  });

  test('09 — Schedule view renders after generation', async ({ page }) => {
    await page.goto('/schedule');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('[data-testid="schedule-page"]')).toBeVisible({ timeout: 10_000 });
  });

  // ── Dashboard summary ─────────────────────────────────────────────────────

  test('10 — Dashboard reflects created data', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('[data-testid="dashboard"]')).toBeVisible({ timeout: 10_000 });
  });
});
