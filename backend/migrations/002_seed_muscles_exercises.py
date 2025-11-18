from yoyo import step

up_sql = r"""
-- 1) Insert base muscle groups (idempotent)
INSERT INTO muscle_groups (name, name_en, description)
VALUES
  ('грудь', 'chest', 'Группа мышц груди'),
  ('спина', 'back', 'Широчайшие и мышцы спины'),
  ('ноги', 'legs', 'Квадрицепсы, бицепсы бедра, ягодицы, икры'),
  ('плечи', 'shoulders', 'Дельтовидные мышцы'),
  ('руки', 'arms', 'Бицепсы и трицепсы, предплечья'),
  ('пресс', 'core', 'Мышцы кора и пресса')
ON CONFLICT (name) DO NOTHING;

-- 2) Insert exercises (idempotent, set primary_muscle_group_id by name)
-- Chest
INSERT INTO exercises (name, description, primary_muscle_group_id, equipment, is_compound, difficulty_level, video_url, image_url)
SELECT 'Жим штанги лежа', 'Классическое базовое упражнение для развития груди и трицепсов.', (SELECT id FROM muscle_groups WHERE name='грудь'), 'штанга', true, 'новичок', NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM exercises WHERE name = 'Жим штанги лежа');

INSERT INTO exercises (name, description, primary_muscle_group_id, equipment, is_compound, difficulty_level, video_url, image_url)
SELECT 'Жим под углом (кладь/наклон)', 'Наклонный жим для верхней части груди.', (SELECT id FROM muscle_groups WHERE name='грудь'), 'штанга/гантели', true, 'средний', NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM exercises WHERE name = 'Жим под углом (кладь/наклон)');

INSERT INTO exercises (name, description, primary_muscle_group_id, equipment, is_compound, difficulty_level, video_url, image_url)
SELECT 'Разведения гантелей лежа (флай)', 'Изолирующее движение для растягивания и сокращения грудных мышц.', (SELECT id FROM muscle_groups WHERE name='грудь'), 'гантели', false, 'новичок', NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM exercises WHERE name = 'Разведения гантелей лежа (флай)');

INSERT INTO exercises (name, description, primary_muscle_group_id, equipment, is_compound, difficulty_level, video_url, image_url)
SELECT 'Отжимания от пола', 'Базовое упражнение без инвентаря для груди/трицепсов/плеч.', (SELECT id FROM muscle_groups WHERE name='грудь'), 'без оборудования', true, 'новичок', NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM exercises WHERE name = 'Отжимания от пола');

INSERT INTO exercises (name, description, primary_muscle_group_id, equipment, is_compound, difficulty_level, video_url, image_url)
SELECT 'Кроссовер (сведение в кроссовере)', 'Изолирующее движение на кроссовере для внутренней части груди.', (SELECT id FROM muscle_groups WHERE name='грудь'), 'тренажер', false, 'новичок', NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM exercises WHERE name = 'Кроссовер (сведение в кроссовере)');

-- Back
INSERT INTO exercises (name, description, primary_muscle_group_id, equipment, is_compound, difficulty_level, video_url, image_url)
SELECT 'Тяга штанги в наклоне', 'Базовая тяга для толщины спины и задних дельт.', (SELECT id FROM muscle_groups WHERE name='спина'), 'штанга', true, 'средний', NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM exercises WHERE name = 'Тяга штанги в наклоне');

INSERT INTO exercises (name, description, primary_muscle_group_id, equipment, is_compound, difficulty_level, video_url, image_url)
SELECT 'Мёртвая тяга (становая)', 'Флагманское базовое упражнение для спины, ног и корпуса.', (SELECT id FROM muscle_groups WHERE name='спина'), 'штанга', true, 'продвинутый', NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM exercises WHERE name = 'Мёртвая тяга (становая)');

INSERT INTO exercises (name, description, primary_muscle_group_id, equipment, is_compound, difficulty_level, video_url, image_url)
SELECT 'Подтягивания', 'Классическое упражнение для широчайших и силы верхней части тела.', (SELECT id FROM muscle_groups WHERE name='спина'), 'турник', true, 'средний', NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM exercises WHERE name = 'Подтягивания');

INSERT INTO exercises (name, description, primary_muscle_group_id, equipment, is_compound, difficulty_level, video_url, image_url)
SELECT 'Тяга верхнего блока', 'Альтернатива подтягиваниям на тренажёре (локализованная нагрузка на широчайшие).', (SELECT id FROM muscle_groups WHERE name='спина'), 'тренажер', true, 'новичок', NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM exercises WHERE name = 'Тяга верхнего блока');

INSERT INTO exercises (name, description, primary_muscle_group_id, equipment, is_compound, difficulty_level, video_url, image_url)
SELECT 'Тяга горизонтального блока (гребля сидя)', 'Горизонтальная тяга для средней части спины.', (SELECT id FROM muscle_groups WHERE name='спина'), 'тренажер', true, 'новичок', NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM exercises WHERE name = 'Тяга горизонтального блока (гребля сидя)');

-- Legs
INSERT INTO exercises (name, description, primary_muscle_group_id, equipment, is_compound, difficulty_level, video_url, image_url)
SELECT 'Приседания со штангой', 'Базовое упражнение для квадрицепсов, ягодиц и кора.', (SELECT id FROM muscle_groups WHERE name='ноги'), 'штанга', true, 'средний', NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM exercises WHERE name = 'Приседания со штангой');

INSERT INTO exercises (name, description, primary_muscle_group_id, equipment, is_compound, difficulty_level, video_url, image_url)
SELECT 'Фронтальные приседания', 'Приседания с штангой на груди — больше нагружают квадрицепс.', (SELECT id FROM muscle_groups WHERE name='ноги'), 'штанга', true, 'средний', NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM exercises WHERE name = 'Фронтальные приседания');

INSERT INTO exercises (name, description, primary_muscle_group_id, equipment, is_compound, difficulty_level, video_url, image_url)
SELECT 'Жим ногами', 'Тренажёрный жим для квадрицепсов и ягодиц.', (SELECT id FROM muscle_groups WHERE name='ноги'), 'тренажер', true, 'новичок', NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM exercises WHERE name = 'Жим ногами');

INSERT INTO exercises (name, description, primary_muscle_group_id, equipment, is_compound, difficulty_level, video_url, image_url)
SELECT 'Румынская тяга', 'Упражнение для задней поверхности бедра и ягодиц.', (SELECT id FROM muscle_groups WHERE name='ноги'), 'штанга/гантели', true, 'средний', NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM exercises WHERE name = 'Румынская тяга');

INSERT INTO exercises (name, description, primary_muscle_group_id, equipment, is_compound, difficulty_level, video_url, image_url)
SELECT 'Выпады (шаговые)', 'Выпады для квадрицепсов и ягодиц, можно с гантелями.', (SELECT id FROM muscle_groups WHERE name='ноги'), 'гантели', true, 'новичок', NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM exercises WHERE name = 'Выпады (шаговые)');

INSERT INTO exercises (name, description, primary_muscle_group_id, equipment, is_compound, difficulty_level, video_url, image_url)
SELECT 'Подъёмы на носки (икры)', 'Изолирующее движение для икроножных мышц.', (SELECT id FROM muscle_groups WHERE name='ноги'), 'без оборудования/тренажер', false, 'новичок', NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM exercises WHERE name = 'Подъёмы на носки (икры)');

-- Shoulders
INSERT INTO exercises (name, description, primary_muscle_group_id, equipment, is_compound, difficulty_level, video_url, image_url)
SELECT 'Жим штанги сидя (армейский жим)', 'Базовый жим для передней и средней дельты.', (SELECT id FROM muscle_groups WHERE name='плечи'), 'штанга', true, 'средний', NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM exercises WHERE name = 'Жим штанги сидя (армейский жим)');

INSERT INTO exercises (name, description, primary_muscle_group_id, equipment, is_compound, difficulty_level, video_url, image_url)
SELECT 'Разведения рук в стороны (боковые)', 'Изолирующее упражнение для средней дельты.', (SELECT id FROM muscle_groups WHERE name='плечи'), 'гантели', false, 'новичок', NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM exercises WHERE name = 'Разведения рук в стороны (боковые)');

INSERT INTO exercises (name, description, primary_muscle_group_id, equipment, is_compound, difficulty_level, video_url, image_url)
SELECT 'Передние подъёмы гантелей', 'Целенаправленная работа на переднюю дельту.', (SELECT id FROM muscle_groups WHERE name='плечи'), 'гантели', false, 'новичок', NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM exercises WHERE name = 'Передние подъёмы гантелей');

INSERT INTO exercises (name, description, primary_muscle_group_id, equipment, is_compound, difficulty_level, video_url, image_url)
SELECT 'Обратные разведения (задняя дельта)', 'Укрепляет заднюю дельту и верхнюю часть спины.', (SELECT id FROM muscle_groups WHERE name='плечи'), 'гантели/тренажер', false, 'новичок', NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM exercises WHERE name = 'Обратные разведения (задняя дельта)');

-- Arms
INSERT INTO exercises (name, description, primary_muscle_group_id, equipment, is_compound, difficulty_level, video_url, image_url)
SELECT 'Подъём штанги на бицепс', 'Классический подъём для бицепсов.', (SELECT id FROM muscle_groups WHERE name='руки'), 'штанга', false, 'новичок', NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM exercises WHERE name = 'Подъём штанги на бицепс');

INSERT INTO exercises (name, description, primary_muscle_group_id, equipment, is_compound, difficulty_level, video_url, image_url)
SELECT 'Подъём гантелей (молоток)', 'Упражнение для брахиалиса и предплечья.', (SELECT id FROM muscle_groups WHERE name='руки'), 'гантели', false, 'новичок', NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM exercises WHERE name = 'Подъём гантелей (молоток)');

INSERT INTO exercises (name, description, primary_muscle_group_id, equipment, is_compound, difficulty_level, video_url, image_url)
SELECT 'Французский жим лежа (трицепс)', 'Изолирующее упражнение на трицепс.', (SELECT id FROM muscle_groups WHERE name='руки'), 'штанга/гантели', false, 'новичок', NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM exercises WHERE name = 'Французский жим лежа (трицепс)');

INSERT INTO exercises (name, description, primary_muscle_group_id, equipment, is_compound, difficulty_level, video_url, image_url)
SELECT 'Жим узким хватом', 'Базовое упражнение, нагружает трицепс и грудь.', (SELECT id FROM muscle_groups WHERE name='руки'), 'штанга', true, 'средний', NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM exercises WHERE name = 'Жим узким хватом');

-- Core / Abs
INSERT INTO exercises (name, description, primary_muscle_group_id, equipment, is_compound, difficulty_level, video_url, image_url)
SELECT 'Планка', 'Статическое упражнение для кора и стабильности.', (SELECT id FROM muscle_groups WHERE name='пресс'), 'без оборудования', false, 'новичок', NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM exercises WHERE name = 'Планка');

INSERT INTO exercises (name, description, primary_muscle_group_id, equipment, is_compound, difficulty_level, video_url, image_url)
SELECT 'Русский твист', 'Динамическое скручивание для косых мышц живота.', (SELECT id FROM muscle_groups WHERE name='пресс'), 'без оборудования/гантель', false, 'новичок', NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM exercises WHERE name = 'Русский твист');

INSERT INTO exercises (name, description, primary_muscle_group_id, equipment, is_compound, difficulty_level, video_url, image_url)
SELECT 'Подъёмы ног в висе', 'Упражнение для нижнего пресса и сгибателей бедра.', (SELECT id FROM muscle_groups WHERE name='пресс'), 'турник', false, 'средний', NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM exercises WHERE name = 'Подъёмы ног в висе');

-- Дополнительные (чтобы >=25)
INSERT INTO exercises (name, description, primary_muscle_group_id, equipment, is_compound, difficulty_level, video_url, image_url)
SELECT 'Хип Траст (подъём таза)', 'Упражнение для ягодиц и задней поверхности бедра.', (SELECT id FROM muscle_groups WHERE name='ноги'), 'штанга/платформа', true, 'средний', NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM exercises WHERE name = 'Хип Траст (подъём таза)');

INSERT INTO exercises (name, description, primary_muscle_group_id, equipment, is_compound, difficulty_level, video_url, image_url)
SELECT 'Тяга Т-грифа', 'Вариант тяги для средней и нижней части спины.', (SELECT id FROM muscle_groups WHERE name='спина'), 'штанга/Т-гриф', true, 'средний', NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM exercises WHERE name = 'Тяга Т-грифа');

INSERT INTO exercises (name, description, primary_muscle_group_id, equipment, is_compound, difficulty_level, video_url, image_url)
SELECT 'Подъёмы туловища (скручивания)', 'Базовые скручивания для верхнего пресса.', (SELECT id FROM muscle_groups WHERE name='пресс'), 'без оборудования', false, 'новичок', NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM exercises WHERE name = 'Подъёмы туловища (скручивания)');

"""

down_sql = r"""
-- Удаляем добавленные упражнения и группы мышц в обратном порядке
DELETE FROM exercises WHERE name IN (
  'Жим штанги лежа',
  'Жим под углом (кладь/наклон)',
  'Разведения гантелей лежа (флай)',
  'Отжимания от пола',
  'Кроссовер (сведение в кроссовере)',
  'Тяга штанги в наклоне',
  'Мёртвая тяга (становая)',
  'Подтягивания',
  'Тяга верхнего блока',
  'Тяга горизонтального блока (гребля сидя)',
  'Приседания со штангой',
  'Фронтальные приседания',
  'Жим ногами',
  'Румынская тяга',
  'Выпады (шаговые)',
  'Подъёмы на носки (икры)',
  'Жим штанги сидя (армейский жим)',
  'Разведения рук в стороны (боковые)',
  'Передние подъёмы гантелей',
  'Обратные разведения (задняя дельта)',
  'Подъём штанги на бицепс',
  'Подъём гантелей (молоток)',
  'Французский жим лежа (трицепс)',
  'Жим узким хватом',
  'Планка',
  'Русский твист',
  'Подъёмы ног в висе',
  'Хип Траст (подъём таза)',
  'Тяга Т-грифа',
  'Подъёмы туловища (скручивания)'
);

DELETE FROM muscle_groups WHERE name IN (
  'грудь','спина','ноги','плечи','руки','пресс'
);
"""

steps = [step(up_sql, down_sql)]