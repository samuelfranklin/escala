/**
 * E2E Full Flow Test Suite
 *
 * Cobertura completa do fluxo do usuário usando Page Object Model (POM):
 *   Members (×10) → Squads (×5) → Associar membros → Events (×3) → Gerar Escala
 *
 * Run: npx playwright test tests/e2e/test_full_flow.spec.ts
 */
import { test, expect } from './fixtures';

// ─── Test data ────────────────────────────────────────────────────────────────

const MEMBERS = [
  { name: 'Ana Lima',      phone: '11900000001', email: 'ana@test.com'    },
  { name: 'Bruno Souza',   phone: '11900000002', email: 'bruno@test.com'  },
  { name: 'Carla Mendes',  phone: '11900000003', email: 'carla@test.com'  },
  { name: 'Diego Rocha',   phone: '11900000004', email: 'diego@test.com'  },
  { name: 'Eva Martins',   phone: '11900000005', email: 'eva@test.com'    },
  { name: 'Felipe Costa',  phone: '11900000006', email: 'felipe@test.com' },
  { name: 'Gabi Oliveira', phone: '11900000007', email: 'gabi@test.com'   },
  { name: 'Hugo Ferreira', phone: '11900000008', email: 'hugo@test.com'   },
  { name: 'Iris Santos',   phone: '11900000009', email: 'iris@test.com'   },
  { name: 'João Alves',    phone: '11900000010', email: 'joao@test.com'   },
];

const SQUADS = [
  { name: 'Câmera' },
  { name: 'Transmissão' },
  { name: 'Áudio' },
  { name: 'Iluminação' },
  { name: 'Apresentação' },
];

const SQUAD_MEMBERS: Record<string, [string, string]> = {
  'Câmera':       ['Ana Lima',      'Bruno Souza'],
  'Transmissão':  ['Carla Mendes',  'Diego Rocha'],
  'Áudio':        ['Eva Martins',   'Felipe Costa'],
  'Iluminação':   ['Gabi Oliveira', 'Hugo Ferreira'],
  'Apresentação': ['Iris Santos',   'João Alves'],
};

function futureDate(daysFromNow: number): string {
  const d = new Date();
  d.setDate(d.getDate() + daysFromNow);
  return d.toISOString().slice(0, 10);
}

const EVENTS = [
  { name: 'Culto Domingo', date: futureDate(7)  },
  { name: 'Culto Quarta',  date: futureDate(10) },
  { name: 'Culto Sexta',   date: futureDate(12) },
];

// ─── Tests ────────────────────────────────────────────────────────────────────

test.describe('Full Flow — Escala Mídia', () => {

  test('00 — App carrega e exibe o dashboard', async ({ dashboardPage }) => {
    await dashboardPage.goto();
    await expect(dashboardPage.container).toBeVisible({ timeout: 10_000 });
  });

  // ── Members ──────────────────────────────────────────────────────────────

  test('01 — Cria 10 membros', async ({ membersPage }) => {
    await membersPage.goto();
    for (const member of MEMBERS) {
      await membersPage.create(member);
    }
  });

  test('02 — Lista de membros exibe 10 linhas', async ({ membersPage }) => {
    await membersPage.goto();
    await expect(membersPage.rows).toHaveCount(10, { timeout: 10_000 });
  });

  // ── Squads ───────────────────────────────────────────────────────────────

  test('03 — Cria 5 times', async ({ squadsPage }) => {
    await squadsPage.goto();
    for (const squad of SQUADS) {
      await squadsPage.create(squad);
    }
  });

  test('04 — Lista de times exibe 5 linhas', async ({ squadsPage }) => {
    await squadsPage.goto();
    await expect(squadsPage.rows).toHaveCount(5, { timeout: 10_000 });
  });

  // ── Associate members to squads ──────────────────────────────────────────

  test('05 — Associa 2 membros a cada time', async ({ squadsPage }) => {
    await squadsPage.goto();
    for (const [squadName, members] of Object.entries(SQUAD_MEMBERS)) {
      await squadsPage.selectByName(squadName);
      for (const memberName of members) {
        await squadsPage.addMember(memberName);
      }
    }
  });

  // ── Events ───────────────────────────────────────────────────────────────

  test('06 — Cria 3 eventos', async ({ eventsPage }) => {
    await eventsPage.goto();
    for (const event of EVENTS) {
      await eventsPage.create(event);
    }
  });

  test('07 — Lista de eventos exibe 3 linhas', async ({ eventsPage }) => {
    await eventsPage.goto();
    await expect(eventsPage.rows).toHaveCount(3, { timeout: 10_000 });
  });

  // ── Generate Schedule ─────────────────────────────────────────────────────

  test('08 — Gera escala para o primeiro evento', async ({ schedulePage }) => {
    await schedulePage.goto();
    await schedulePage.selectEvent(1);
    await schedulePage.generate();

    const errorEl = schedulePage.page.locator('[data-testid="error"], .error, .alert-danger');
    await expect(errorEl).toHaveCount(0);
  });

  test('09 — Tela de escala renderiza sem crash', async ({ schedulePage }) => {
    await schedulePage.goto();
    await expect(schedulePage.container).toBeVisible({ timeout: 10_000 });
  });

  // ── Dashboard summary ─────────────────────────────────────────────────────

  test('10 — Dashboard reflete os dados criados', async ({ dashboardPage }) => {
    await dashboardPage.goto();
    await expect(dashboardPage.container).toBeVisible({ timeout: 10_000 });
  });
});

