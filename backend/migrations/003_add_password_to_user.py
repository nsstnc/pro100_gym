from yoyo import step

__depends__ = {"002_seed_muscles_exercises"}

steps = [
    step(
        """
        ALTER TABLE users
        ADD COLUMN hashed_password VARCHAR(255) NOT NULL;
        """,
        "ALTER TABLE users DROP COLUMN hashed_password;"
    ),
    step(
        """
        ALTER TABLE users
        ALTER COLUMN email SET NOT NULL;
        """,
        "ALTER TABLE users ALTER COLUMN email DROP NOT NULL;"
    ),
    step(
        """
        ALTER TABLE users
        ADD CONSTRAINT uq_users_username UNIQUE (username);
        """,
        "ALTER TABLE users DROP CONSTRAINT uq_users_username;"
    ),
    step(
        """
        CREATE INDEX ix_users_email ON users (email);
        """,
        "DROP INDEX ix_users_email;"
    )
]
