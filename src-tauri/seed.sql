-- Seed: Time de Mídia — dados reais
-- Limpa banco (ordem reversa de dependência)
PRAGMA foreign_keys = OFF;
DELETE FROM schedule_entries;
DELETE FROM availability;
DELETE FROM couples;
DELETE FROM event_squads;
DELETE FROM events;
DELETE FROM members_squads;
DELETE FROM squads;
DELETE FROM members;
PRAGMA foreign_keys = ON;

-- ═══════════════════════════════════════
-- SQUADS
-- ═══════════════════════════════════════
INSERT INTO squads (id, name, description) VALUES
  ('sq-telao',       'Telão',       'Operação de slides e projeção'),
  ('sq-luzes',       'Luzes',       'Iluminação do ambiente'),
  ('sq-som',         'Som',         'Mesa de som e equipamentos de áudio'),
  ('sq-fotografia',  'Fotografia',  'Registro fotográfico dos eventos'),
  ('sq-storys',      'Storys',      'Stories e conteúdo rápido para redes sociais'),
  ('sq-transmissao',  'Transmissão', 'Operação de PC para transmissão ao vivo'),
  ('sq-filmagem',     'Filmagem',    'Operação de câmeras para transmissão ao vivo');

-- ═══════════════════════════════════════
-- MEMBERS
-- ═══════════════════════════════════════
-- Telão
INSERT INTO members (id, name, rank) VALUES ('m-alex-silva',       'Alex Silva',        'member');
INSERT INTO members (id, name, rank) VALUES ('m-amanda-gabrielle', 'Amanda Gabrielle',  'member');
INSERT INTO members (id, name, rank) VALUES ('m-kesia-morais',     'Késia Morais',      'member');
INSERT INTO members (id, name, rank) VALUES ('m-lucas-silva',      'Lucas Silva',       'leader');
INSERT INTO members (id, name, rank) VALUES ('m-ramon-mendes',     'Ramon Mendes',      'member');
INSERT INTO members (id, name, rank) VALUES ('m-yago-cesar',       'Yago Cesar',        'member');
INSERT INTO members (id, name, rank) VALUES ('m-vanessa-melina',   'Vanessa Melina',    'recruit');

-- Luzes
INSERT INTO members (id, name, rank) VALUES ('m-gabriel-toledo',   'Gabriel Toledo',    'member');
INSERT INTO members (id, name, rank) VALUES ('m-mateus-trindade',  'Mateus Trindade',   'member');
INSERT INTO members (id, name, rank) VALUES ('m-nata-moreira',     'Natã Moreira',      'leader');
INSERT INTO members (id, name, rank) VALUES ('m-paulo',            'Paulo',             'recruit');

-- Som
INSERT INTO members (id, name, rank) VALUES ('m-arthur-porto',     'Arthur Porto',      'member');
INSERT INTO members (id, name, rank) VALUES ('m-rafael-marinho',   'Rafael Marinho',    'member');
INSERT INTO members (id, name, rank) VALUES ('m-mateus-gomes',     'Mateus Gomes',      'member');

-- Fotografia (Thales, Diogo, Bianca, Marcela, Camila — Késia já existe)
INSERT INTO members (id, name, rank) VALUES ('m-thales-augusto',   'Thales Augusto',    'member');
INSERT INTO members (id, name, rank) VALUES ('m-diogo-alessandro', 'Diogo Alessandro',  'member');
INSERT INTO members (id, name, rank) VALUES ('m-bianca-caroline',  'Bianca Caroline',   'member');
INSERT INTO members (id, name, rank) VALUES ('m-marcela',          'Marcela',           'recruit');
INSERT INTO members (id, name, rank) VALUES ('m-camila',           'Camila',            'recruit');

-- Storys
INSERT INTO members (id, name, rank) VALUES ('m-gustavo-helcio',   'Gustavo Helcio',    'member');
INSERT INTO members (id, name, rank) VALUES ('m-priscila-araujo',  'Priscila Araújo',   'member');
INSERT INTO members (id, name, rank) VALUES ('m-livia-nesio',      'Lívia Nesio',       'member');

-- Transmissão (PC) / Filmagem (Câmera)
INSERT INTO members (id, name, rank) VALUES ('m-christian-diego',  'Christian Diego',   'member');
INSERT INTO members (id, name, rank) VALUES ('m-matheus-sales',    'Matheus Sales',     'member');
INSERT INTO members (id, name, rank) VALUES ('m-deise-amorim',     'Deise Amorim',      'member');
INSERT INTO members (id, name, rank) VALUES ('m-maria-eduarda',    'Maria Eduarda',     'recruit');
INSERT INTO members (id, name, rank) VALUES ('m-atila-costa',      'Átila Costa',       'member');
INSERT INTO members (id, name, rank) VALUES ('m-leyse-gualberto',  'Leyse Gualberto',   'member');

-- ═══════════════════════════════════════
-- MEMBERS_SQUADS (vinculação membro ↔ time)
-- ═══════════════════════════════════════
-- Telão
INSERT INTO members_squads (member_id, squad_id) VALUES ('m-alex-silva',       'sq-telao');
INSERT INTO members_squads (member_id, squad_id) VALUES ('m-amanda-gabrielle', 'sq-telao');
INSERT INTO members_squads (member_id, squad_id) VALUES ('m-kesia-morais',     'sq-telao');
INSERT INTO members_squads (member_id, squad_id) VALUES ('m-lucas-silva',      'sq-telao');
INSERT INTO members_squads (member_id, squad_id) VALUES ('m-ramon-mendes',     'sq-telao');
INSERT INTO members_squads (member_id, squad_id) VALUES ('m-yago-cesar',       'sq-telao');
INSERT INTO members_squads (member_id, squad_id) VALUES ('m-vanessa-melina',   'sq-telao');

-- Luzes
INSERT INTO members_squads (member_id, squad_id) VALUES ('m-gabriel-toledo',   'sq-luzes');
INSERT INTO members_squads (member_id, squad_id) VALUES ('m-mateus-trindade',  'sq-luzes');
INSERT INTO members_squads (member_id, squad_id) VALUES ('m-nata-moreira',     'sq-luzes');
INSERT INTO members_squads (member_id, squad_id) VALUES ('m-paulo',            'sq-luzes');

-- Som
INSERT INTO members_squads (member_id, squad_id) VALUES ('m-arthur-porto',     'sq-som');
INSERT INTO members_squads (member_id, squad_id) VALUES ('m-rafael-marinho',   'sq-som');
INSERT INTO members_squads (member_id, squad_id) VALUES ('m-mateus-gomes',     'sq-som');

-- Fotografia
INSERT INTO members_squads (member_id, squad_id) VALUES ('m-thales-augusto',   'sq-fotografia');
INSERT INTO members_squads (member_id, squad_id) VALUES ('m-kesia-morais',     'sq-fotografia');
INSERT INTO members_squads (member_id, squad_id) VALUES ('m-diogo-alessandro', 'sq-fotografia');
INSERT INTO members_squads (member_id, squad_id) VALUES ('m-bianca-caroline',  'sq-fotografia');
INSERT INTO members_squads (member_id, squad_id) VALUES ('m-marcela',          'sq-fotografia');
INSERT INTO members_squads (member_id, squad_id) VALUES ('m-camila',           'sq-fotografia');

-- Storys
INSERT INTO members_squads (member_id, squad_id) VALUES ('m-gustavo-helcio',   'sq-storys');
INSERT INTO members_squads (member_id, squad_id) VALUES ('m-priscila-araujo',  'sq-storys');
INSERT INTO members_squads (member_id, squad_id) VALUES ('m-livia-nesio',      'sq-storys');

-- Transmissão (PC)
INSERT INTO members_squads (member_id, squad_id) VALUES ('m-christian-diego',  'sq-transmissao');
INSERT INTO members_squads (member_id, squad_id) VALUES ('m-matheus-sales',    'sq-transmissao');
INSERT INTO members_squads (member_id, squad_id) VALUES ('m-maria-eduarda',    'sq-transmissao');

-- Filmagem (Câmera)
INSERT INTO members_squads (member_id, squad_id) VALUES ('m-matheus-sales',    'sq-filmagem');
INSERT INTO members_squads (member_id, squad_id) VALUES ('m-deise-amorim',     'sq-filmagem');
INSERT INTO members_squads (member_id, squad_id) VALUES ('m-maria-eduarda',    'sq-filmagem');
INSERT INTO members_squads (member_id, squad_id) VALUES ('m-atila-costa',      'sq-filmagem');
INSERT INTO members_squads (member_id, squad_id) VALUES ('m-leyse-gualberto',  'sq-filmagem');

-- ═══════════════════════════════════════
-- EVENTS (recorrentes)
-- ═══════════════════════════════════════
-- day_of_week: 0=Domingo, 1=Segunda, ..., 3=Quarta, 6=Sábado

-- Culto de Domingo (manhã) — som, telão, fotografia, storys
INSERT INTO events (id, name, event_type, day_of_week, recurrence) VALUES
  ('ev-domingo-manha', 'Culto Domingo Manhã', 'regular', 0, 'weekly');

-- Culto de Domingo (noite) — live
INSERT INTO events (id, name, event_type, day_of_week, recurrence) VALUES
  ('ev-domingo-noite', 'Culto Domingo Noite', 'regular', 0, 'weekly');

-- Culto de Quarta (manhã) — som, telão, storys
INSERT INTO events (id, name, event_type, day_of_week, recurrence) VALUES
  ('ev-quarta-manha', 'Culto Quarta', 'regular', 3, 'weekly');

-- Culto de Quarta (noite) — live
INSERT INTO events (id, name, event_type, day_of_week, recurrence) VALUES
  ('ev-quarta-noite', 'Culto Quarta Noite', 'regular', 3, 'weekly');

-- GDNA Sábado — som, telão, fotografia, storys
INSERT INTO events (id, name, event_type, day_of_week, recurrence) VALUES
  ('ev-gdna-sabado', 'GDNA Sábado', 'regular', 6, 'weekly');

-- ═══════════════════════════════════════
-- EVENT_SQUADS (quais times em cada evento)
-- ═══════════════════════════════════════

-- Culto Domingo Manhã: som(1), telão(1), fotografia(1), storys(1)
INSERT INTO event_squads (event_id, squad_id, min_members, max_members) VALUES ('ev-domingo-manha', 'sq-som',        1, 1);
INSERT INTO event_squads (event_id, squad_id, min_members, max_members) VALUES ('ev-domingo-manha', 'sq-telao',      1, 1);
INSERT INTO event_squads (event_id, squad_id, min_members, max_members) VALUES ('ev-domingo-manha', 'sq-fotografia', 1, 1);
INSERT INTO event_squads (event_id, squad_id, min_members, max_members) VALUES ('ev-domingo-manha', 'sq-storys',     1, 1);

-- Culto Domingo Noite: transmissão(1) + filmagem(1)
INSERT INTO event_squads (event_id, squad_id, min_members, max_members) VALUES ('ev-domingo-noite', 'sq-transmissao', 1, 1);
INSERT INTO event_squads (event_id, squad_id, min_members, max_members) VALUES ('ev-domingo-noite', 'sq-filmagem',    1, 1);

-- Culto Quarta: som(1), telão(1), storys(1)
INSERT INTO event_squads (event_id, squad_id, min_members, max_members) VALUES ('ev-quarta-manha', 'sq-som',    1, 1);
INSERT INTO event_squads (event_id, squad_id, min_members, max_members) VALUES ('ev-quarta-manha', 'sq-telao',  1, 1);
INSERT INTO event_squads (event_id, squad_id, min_members, max_members) VALUES ('ev-quarta-manha', 'sq-storys', 1, 1);

-- Culto Quarta Noite: transmissão(1) + filmagem(1)
INSERT INTO event_squads (event_id, squad_id, min_members, max_members) VALUES ('ev-quarta-noite', 'sq-transmissao', 1, 1);
INSERT INTO event_squads (event_id, squad_id, min_members, max_members) VALUES ('ev-quarta-noite', 'sq-filmagem',    1, 1);

-- GDNA Sábado: som(1), telão(1), fotografia(1), storys(1)
INSERT INTO event_squads (event_id, squad_id, min_members, max_members) VALUES ('ev-gdna-sabado', 'sq-som',        1, 1);
INSERT INTO event_squads (event_id, squad_id, min_members, max_members) VALUES ('ev-gdna-sabado', 'sq-telao',      1, 1);
INSERT INTO event_squads (event_id, squad_id, min_members, max_members) VALUES ('ev-gdna-sabado', 'sq-fotografia', 1, 1);
INSERT INTO event_squads (event_id, squad_id, min_members, max_members) VALUES ('ev-gdna-sabado', 'sq-storys',     1, 1);

-- ═══════════════════════════════════════
-- SCHEDULE_CONFIG (garante que existe)
-- ═══════════════════════════════════════
INSERT OR IGNORE INTO schedule_config (id) VALUES (1);
