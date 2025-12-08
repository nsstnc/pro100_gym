from yoyo import step

steps = [
    step(
        "ALTER TABLE workout_plans ADD CONSTRAINT uq_user_id UNIQUE (user_id);",
        "ALTER TABLE workout_plans DROP CONSTRAINT uq_user_id;",
    ),
    step(
        "ALTER TABLE workout_plans DROP COLUMN is_active;",
        "ALTER TABLE workout_plans ADD COLUMN is_active BOOLEAN DEFAULT TRUE;",
    ),
]
