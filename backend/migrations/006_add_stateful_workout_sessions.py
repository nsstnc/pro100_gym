from yoyo import step

__depends__ = {'005_add_preference_tables'}

steps = [
    step(
        """
        -- Remove the old JSONB exercises column from workout_sessions
        ALTER TABLE workout_sessions DROP COLUMN exercises;

        -- Create the new session status type if it doesn't exist
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'sessionstatus') THEN
                CREATE TYPE sessionstatus AS ENUM ('PENDING', 'IN_PROGRESS', 'COMPLETED', 'SKIPPED');
            END IF;
        END$$;

        -- Add status column to workout_sessions
        ALTER TABLE workout_sessions ADD COLUMN status sessionstatus NOT NULL DEFAULT 'IN_PROGRESS';

        -- Create the session_days table
        CREATE TABLE session_days (
            id SERIAL PRIMARY KEY,
            workout_session_id INTEGER NOT NULL REFERENCES workout_sessions(id) ON DELETE CASCADE,
            plan_day_name VARCHAR(200) NOT NULL,
            "order" INTEGER NOT NULL,
            status sessionstatus NOT NULL DEFAULT 'PENDING'
        );

        -- Create the session_exercises table
        CREATE TABLE session_exercises (
            id SERIAL PRIMARY KEY,
            session_day_id INTEGER NOT NULL REFERENCES session_days(id) ON DELETE CASCADE,
            plan_exercise_name VARCHAR(200) NOT NULL,
            "order" INTEGER NOT NULL,
            status sessionstatus NOT NULL DEFAULT 'PENDING'
        );

        -- Create the session_sets table
        CREATE TABLE session_sets (
            id SERIAL PRIMARY KEY,
            session_exercise_id INTEGER NOT NULL REFERENCES session_exercises(id) ON DELETE CASCADE,
            "order" INTEGER NOT NULL,
            status sessionstatus NOT NULL DEFAULT 'PENDING',
            plan_reps_min INTEGER,
            plan_reps_max INTEGER,
            plan_weight NUMERIC(6, 2),
            reps_done INTEGER,
            weight_lifted NUMERIC(6, 2)
        );
        """,
        """
        -- Revert changes in reverse order

        -- Drop the new tables
        DROP TABLE IF EXISTS session_sets;
        DROP TABLE IF EXISTS session_exercises;
        DROP TABLE IF EXISTS session_days;

        -- Remove status column from workout_sessions
        ALTER TABLE workout_sessions DROP COLUMN status;

        -- Drop the session status type
        DROP TYPE IF EXISTS sessionstatus;

        -- Re-add the exercises JSONB column to workout_sessions
        ALTER TABLE workout_sessions ADD COLUMN exercises JSONB NOT NULL DEFAULT '[]'::jsonb;
        """
    )
]
