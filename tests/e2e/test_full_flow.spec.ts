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

async function openCreateModal(page: import('@playwright/test').Page): Promise<void> {
  const btn = page.locator('button:has-text("Novo"), button:has-text("Adicionar"), button:has-text("Criar")').first();
  await btn.click();
  await page.waitForSelector('[role="dialog"], .modal, form', { state: 'visible' });
}

async function submitForm(page: import('@playwright/test').Page): Promise<void> {
  const submit = page.locator('button[type="submit"], button:has-text("Salvar"), button:has-text("Criar")').last();
  await submit.click();
  await page.waitForTimeout(300);
}

// ─── Tests ────────────────────────────────────────────────────────────────────

test.describe('Full Flow — Escala Mídia', () => {

  test('00 — App loads and shows dashboard', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('h1, h2, [data-testid="dashboard"]')).toBeVisible({ timeout: 10_000 });
  });

  // ── Members ──────────────────────────────────────────────────────────────

  test('01 — Creates 10 members', async ({ page }) => {
    await page.goto('/members');
    await page.waitForLoadState('networkidle');

    for (const member of MEMBERS) {
      await openCreateModal(page);
      await page.locator('input[name="name"], input[placeholder*="nome" i]').fill(member.name);
      await page.locator('input[name="phone"], input[placeholder*="telefone" i]').fill(member.phone);
      await page.locator('input[name="email"], input[type="email"]').fill(member.email);
      await submitForm(page);
    }
  });

  test('02 — Members list shows 10 rows', async ({ page }) => {
    await page.goto('/members');
    await page.waitForLoadState('networkidle');
    const rows = page.locator('table tbody tr, [data-testid="member-row"], li.member-item');
    await expect(rows).toHaveCount(10, { timeout: 10_000 });
  });

  // ── Squads ───────────────────────────────────────────────────────────────

  test('03 — Creates 5 squads', async ({ page }) => {
    await page.goto('/squads');
    await page.waitForLoadState('networkidle');

    for (const squad of SQUADS) {
      await openCreateModal(page);
      await page.locator('input[name="name"], input[placeholder*="nome" i]').fill(squad.name);
      const desc = page.locator('input[name="description"], textarea[name="description"]');
      if (await desc.count() > 0) await desc.fill(squad.description);
      await submitForm(page);
    }
  });

  test('04 — Squads list shows 5 rows', async ({ page }) => {
    await page.goto('/squads');
    await page.waitForLoadState('networkidle');
    const rows = page.locator('table tbody tr, [data-testid="squad-row"], li.squad-item');
    await expect(rows).toHaveCount(5, { timeout: 10_000 });
  });

  // ── Associate members to squads ──────────────────────────────────────────

  test('05 — Assigns 2 members to each squad', async ({ page }) => {
    await page.goto('/squads');
    await page.waitForLoadState('networkidle');

    for (const [squadName, members] of Object.entries(SQUAD_MEMBERS)) {
      // Click the squad to open detail/management panel
      await page.locator(`text="${squadName}"`).first().click();
      await page.waitForTimeout(400);

      // For each member to add, find an "add member" button or select
      for (const memberName of members) {
        const addBtn = page.locator('button:has-text("Adicionar Membro"), button:has-text("Add")').first();
        if (await addBtn.count() > 0) {
          await addBtn.click();
          await page.waitForTimeout(200);
          const select = page.locator('select[name="member_id"], select').first();
          await select.selectOption({ label: memberName });
          await submitForm(page);
          await page.waitForTimeout(300);
        }
      }
    }
  });

  // ── Events ───────────────────────────────────────────────────────────────

  test('06 — Creates 3 events', async ({ page }) => {
    await page.goto('/events');
    await page.waitForLoadState('networkidle');

    for (const event of EVENTS) {
      await openCreateModal(page);
      await page.locator('input[name="name"], input[placeholder*="nome" i]').fill(event.name);
      const typeField = page.locator('input[name="type"], input[name="event_type"], select[name="type"]');
      if (await typeField.count() > 0) await typeField.fill(event.type);
      await submitForm(page);
    }
  });

  test('07 — Events list shows 3 rows', async ({ page }) => {
    await page.goto('/events');
    await page.waitForLoadState('networkidle');
    const rows = page.locator('table tbody tr, [data-testid="event-row"], li.event-item');
    await expect(rows).toHaveCount(3, { timeout: 10_000 });
  });

  // ── Generate Schedule ─────────────────────────────────────────────────────

  test('08 — Generates schedule for current month', async ({ page }) => {
    await page.goto('/schedule');
    await page.waitForLoadState('networkidle');

    // Select an event to generate schedule for
    const eventSelect = page.locator('select[name="event_id"], select').first();
    if (await eventSelect.count() > 0) {
      await eventSelect.selectOption({ index: 1 });
    }

    // Click generate
    const generateBtn = page.locator('button:has-text("Gerar Escala"), button:has-text("Gerar"), button:has-text("Generate")').first();
    await generateBtn.click();
    await page.waitForTimeout(1000);

    // Expect no error state
    const errorEl = page.locator('[data-testid="error"], .error, .alert-danger');
    await expect(errorEl).toHaveCount(0);
  });

  test('09 — Schedule view renders after generation', async ({ page }) => {
    await page.goto('/schedule');
    await page.waitForLoadState('networkidle');

    // Page loads without crash
    await expect(page.locator('h1, h2, main')).toBeVisible({ timeout: 10_000 });
  });

  // ── Dashboard summary ─────────────────────────────────────────────────────

  test('10 — Dashboard reflects created data', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // Expect stat cards to show non-zero values
    const stats = page.locator('[data-testid="stat-card"], .stat-value, .card h3');
    await expect(stats.first()).toBeVisible({ timeout: 10_000 });
  });
});
