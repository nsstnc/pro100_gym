from yoyo import step

__depends__ = {'004_simplify_workout_plan'}

up_sql = r"""
-- 1. Создание новых таблиц для предпочтений
CREATE TABLE restriction_rules (
    id SERIAL PRIMARY KEY,
    slug VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_restriction_rules_slug ON restriction_rules (slug);

CREATE TABLE muscle_focuses (
    id SERIAL PRIMARY KEY,
    slug VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    muscle_group_id INTEGER NOT NULL REFERENCES muscle_groups(id) ON DELETE CASCADE,
    priority_modifier INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_muscle_focuses_slug ON muscle_focuses (slug);

-- 2. Создание ассоциативных таблиц
CREATE TABLE restriction_rule_exercises_association (
    restriction_rule_id INTEGER REFERENCES restriction_rules(id) ON DELETE CASCADE,
    exercise_id INTEGER REFERENCES exercises(id) ON DELETE CASCADE,
    PRIMARY KEY (restriction_rule_id, exercise_id)
);

CREATE TABLE user_preferences_restriction_rules (
    user_preferences_id INTEGER REFERENCES user_preferences(id) ON DELETE CASCADE,
    restriction_rule_id INTEGER REFERENCES restriction_rules(id) ON DELETE CASCADE,
    PRIMARY KEY (user_preferences_id, restriction_rule_id)
);

CREATE TABLE user_preferences_muscle_focuses (
    user_preferences_id INTEGER REFERENCES user_preferences(id) ON DELETE CASCADE,
    muscle_focus_id INTEGER REFERENCES muscle_focuses(id) ON DELETE CASCADE,
    PRIMARY KEY (user_preferences_id, muscle_focus_id)
);

-- 3. Изменение таблицы user_preferences
ALTER TABLE user_preferences DROP COLUMN IF EXISTS restrictions;
ALTER TABLE user_preferences DROP COLUMN IF EXISTS muscle_preferences;

-- 4. Наполнение таблицы restriction_rules
INSERT INTO restriction_rules (slug, name, description) VALUES
('sore_knees', 'Больные колени', 'Исключает упражнения с высокой осевой нагрузкой на коленные суставы.'),
('sore_back', 'Больная спина', 'Исключает упражнения, создающие значительную нагрузку на позвоночник.'),
('sore_shoulders', 'Больные плечи', 'Исключает жимовые и тяговые движения, которые могут усугубить травмы плеча.')
ON CONFLICT (slug) DO NOTHING;

-- 5. Наполнение таблицы muscle_focuses (примеры)
INSERT INTO muscle_focuses (slug, name, muscle_group_id, priority_modifier)
SELECT 'chest_focus_plus', 'Акцент на грудь', id, 1 FROM muscle_groups WHERE name = 'грудь'
ON CONFLICT (slug) DO NOTHING;

INSERT INTO muscle_focuses (slug, name, muscle_group_id, priority_modifier)
SELECT 'back_focus_plus', 'Акцент на спину', id, 1 FROM muscle_groups WHERE name = 'спина'
ON CONFLICT (slug) DO NOTHING;

INSERT INTO muscle_focuses (slug, name, muscle_group_id, priority_modifier)
SELECT 'legs_focus_plus', 'Акцент на ноги', id, 1 FROM muscle_groups WHERE name = 'ноги'
ON CONFLICT (slug) DO NOTHING;

INSERT INTO muscle_focuses (slug, name, muscle_group_id, priority_modifier)
SELECT 'legs_focus_minus', 'Не хочу качать ноги', id, -1 FROM muscle_groups WHERE name = 'ноги'
ON CONFLICT (slug) DO NOTHING;

INSERT INTO muscle_focuses (slug, name, muscle_group_id, priority_modifier)
SELECT 'arms_focus_plus', 'Акцент на руки', id, 1 FROM muscle_groups WHERE name = 'руки'
ON CONFLICT (slug) DO NOTHING;

-- 6. Связывание правил и упражнений
-- Больные колени
INSERT INTO restriction_rule_exercises_association (restriction_rule_id, exercise_id)
SELECT
    (SELECT id FROM restriction_rules WHERE slug = 'sore_knees'),
    (SELECT id FROM exercises WHERE name = 'Приседания со штангой')
WHERE EXISTS (SELECT 1 FROM exercises WHERE name = 'Приседания со штангой')
ON CONFLICT DO NOTHING;

INSERT INTO restriction_rule_exercises_association (restriction_rule_id, exercise_id)
SELECT
    (SELECT id FROM restriction_rules WHERE slug = 'sore_knees'),
    (SELECT id FROM exercises WHERE name = 'Выпады (шаговые)')
WHERE EXISTS (SELECT 1 FROM exercises WHERE name = 'Выпады (шаговые)')
ON CONFLICT DO NOTHING;

INSERT INTO restriction_rule_exercises_association (restriction_rule_id, exercise_id)
SELECT
    (SELECT id FROM restriction_rules WHERE slug = 'sore_knees'),
    (SELECT id FROM exercises WHERE name = 'Жим ногами')
WHERE EXISTS (SELECT 1 FROM exercises WHERE name = 'Жим ногами')
ON CONFLICT DO NOTHING;

-- Больная спина
INSERT INTO restriction_rule_exercises_association (restriction_rule_id, exercise_id)
SELECT
    (SELECT id FROM restriction_rules WHERE slug = 'sore_back'),
    (SELECT id FROM exercises WHERE name = 'Мёртвая тяга (становая)')
WHERE EXISTS (SELECT 1 FROM exercises WHERE name = 'Мёртвая тяга (становая)')
ON CONFLICT DO NOTHING;

INSERT INTO restriction_rule_exercises_association (restriction_rule_id, exercise_id)
SELECT
    (SELECT id FROM restriction_rules WHERE slug = 'sore_back'),
    (SELECT id FROM exercises WHERE name = 'Приседания со штангой')
WHERE EXISTS (SELECT 1 FROM exercises WHERE name = 'Приседания со штангой')
ON CONFLICT DO NOTHING;

-- Больные плечи
INSERT INTO restriction_rule_exercises_association (restriction_rule_id, exercise_id)
SELECT
    (SELECT id FROM restriction_rules WHERE slug = 'sore_shoulders'),
    (SELECT id FROM exercises WHERE name = 'Жим штанги лежа')
WHERE EXISTS (SELECT 1 FROM exercises WHERE name = 'Жим штанги лежа')
ON CONFLICT DO NOTHING;

INSERT INTO restriction_rule_exercises_association (restriction_rule_id, exercise_id)
SELECT
    (SELECT id FROM restriction_rules WHERE slug = 'sore_shoulders'),
    (SELECT id FROM exercises WHERE name = 'Жим штанги сидя (армейский жим)')
WHERE EXISTS (SELECT 1 FROM exercises WHERE name = 'Жим штанги сидя (армейский жим)')
ON CONFLICT DO NOTHING;
"""

down_sql = r"""
-- 1. Возвращаем столбцы в user_preferences
ALTER TABLE user_preferences ADD COLUMN IF NOT EXISTS restrictions JSONB DEFAULT '[]'::jsonb;
ALTER TABLE user_preferences ADD COLUMN IF NOT EXISTS muscle_preferences JSONB DEFAULT '[]'::jsonb;

-- 2. Удаляем ассоциативные и новые таблицы
DROP TABLE IF EXISTS user_preferences_muscle_focuses;
DROP TABLE IF EXISTS user_preferences_restriction_rules;
DROP TABLE IF EXISTS restriction_rule_exercises_association;
DROP TABLE IF EXISTS muscle_focuses;
DROP TABLE IF EXISTS restriction_rules;
"""

steps = [step(up_sql, down_sql)]
