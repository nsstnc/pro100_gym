from yoyo import step

up_sql = """
CREATE TABLE IF NOT EXISTS muscle_groups (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    name_en VARCHAR(50),
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE,
    email VARCHAR(255) UNIQUE,
    username VARCHAR(100) NOT NULL,
    weight NUMERIC(5,2),
    height INTEGER,
    age INTEGER,
    fitness_goal VARCHAR(50),
    experience_level VARCHAR(50),
    workouts_per_week INTEGER,
    session_duration INTEGER,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS exercises (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    primary_muscle_group_id INTEGER REFERENCES muscle_groups(id) ON DELETE SET NULL,
    equipment VARCHAR(100),
    is_compound BOOLEAN DEFAULT TRUE,
    difficulty_level VARCHAR(30),
    video_url VARCHAR(500),
    image_url VARCHAR(500),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS workout_plans (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    split_type VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    generated_at TIMESTAMPTZ DEFAULT now(),
    expires_at TIMESTAMPTZ,
    days JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS workout_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    workout_plan_id INTEGER REFERENCES workout_plans(id) ON DELETE SET NULL,
    started_at TIMESTAMPTZ DEFAULT now(),
    completed_at TIMESTAMPTZ,
    duration_minutes INTEGER,
    rating INTEGER,
    notes TEXT,
    exercises JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS user_progress (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    weight NUMERIC(5,2),
    body_measurements JSONB,
    notes TEXT,
    recorded_at DATE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS user_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    muscle_preferences JSONB DEFAULT '[]'::jsonb,
    restrictions JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- optional indexes
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users (telegram_id);
CREATE INDEX IF NOT EXISTS idx_exercises_primary_muscle ON exercises (primary_muscle_group_id);
"""

down_sql = """
DROP TABLE IF EXISTS user_preferences CASCADE;
DROP TABLE IF EXISTS user_progress CASCADE;
DROP TABLE IF EXISTS workout_sessions CASCADE;
DROP TABLE IF EXISTS workout_plans CASCADE;
DROP TABLE IF EXISTS exercises CASCADE;
DROP TABLE IF EXISTS muscle_groups CASCADE;
DROP TABLE IF EXISTS users CASCADE;
"""

steps = [
    step(up_sql, down_sql)
]
