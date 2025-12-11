import enum
from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    String,
    Numeric,
    Boolean,
    Text,
    ForeignKey,
    DateTime,
    func,
    text,
    Table,
    Enum as PgEnum,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.db import Base


# --- Enums ---
class SessionStatus(enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


# --- Users (с полями профиля) ---
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), nullable=False, unique=True)
    hashed_password = Column(String, nullable=False)

    weight = Column(Numeric(5, 2), nullable=True)
    height = Column(Integer, nullable=True)
    age = Column(Integer, nullable=True)
    fitness_goal = Column(String(50), nullable=True)
    experience_level = Column(String(50), nullable=True)
    workouts_per_week = Column(Integer, nullable=True)
    session_duration = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("now()"), onupdate=func.now(), nullable=False)

    # relationships
    workout_plans = relationship("WorkoutPlan", back_populates="user", cascade="all, delete-orphan", lazy="selectin")
    workout_sessions = relationship("WorkoutSession", back_populates="user", cascade="all, delete-orphan",
                                    lazy="selectin")
    progress_entries = relationship("UserProgress", back_populates="user", cascade="all, delete-orphan",
                                    lazy="selectin")
    preferences = relationship("UserPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan",
                               lazy="selectin")

    def __repr__(self):
        return f"<User id={self.id} username={self.username!r} telegram_id={self.telegram_id}>"


class MuscleGroup(Base):
    __tablename__ = "muscle_groups"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
    name_en = Column(String(50), nullable=True, unique=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=text("now()"), nullable=False)

    exercises = relationship("Exercise", back_populates="primary_muscle_group", lazy="selectin")

    def __repr__(self):
        return f"<MuscleGroup id={self.id} name={self.name!r}>"


class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False, unique=True)
    description = Column(Text, nullable=True)

    primary_muscle_group_id = Column(Integer, ForeignKey("muscle_groups.id", ondelete="SET NULL"), nullable=True)
    equipment = Column(String(100), nullable=True)
    is_compound = Column(Boolean, default=True)
    difficulty_level = Column(String(30), nullable=True)
    video_url = Column(String(500), nullable=True)
    image_url = Column(String(500), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=text("now()"), nullable=False)

    primary_muscle_group = relationship("MuscleGroup", back_populates="exercises", lazy="joined")
    restricted_in_rules = relationship(
        "RestrictionRule",
        secondary="restriction_rule_exercises_association",
        back_populates="restricted_exercises",
        lazy="selectin"
    )

    def __repr__(self):
        return f"<Exercise id={self.id} name={self.name!r}>"


class WorkoutPlan(Base):
    __tablename__ = "workout_plans"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    name = Column(String(200), nullable=False)
    split_type = Column(String(100), nullable=True)
    generated_at = Column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # days: JSONB structure with list of days and exercises (flexible)
    days = Column(JSONB, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=text("now()"), nullable=False)

    user = relationship("User", back_populates="workout_plans", lazy="joined")

    def __repr__(self):
        return f"<WorkoutPlan id={self.id} name={self.name!r} user_id={self.user_id}>"


class WorkoutSession(Base):
    __tablename__ = "workout_sessions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    workout_plan_id = Column(Integer, ForeignKey("workout_plans.id", ondelete="SET NULL"), nullable=True)

    started_at = Column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    rating = Column(Integer, nullable=True)  # 1-5
    notes = Column(Text, nullable=True)
    status = Column(PgEnum(SessionStatus), nullable=False, default=SessionStatus.IN_PROGRESS)

    created_at = Column(DateTime(timezone=True), server_default=text("now()"), nullable=False)

    user = relationship("User", back_populates="workout_sessions", lazy="joined")
    workout_plan = relationship("WorkoutPlan", lazy="joined")

    # one-to-many relationship to SessionDay
    session_days = relationship("SessionDay", back_populates="session", cascade="all, delete-orphan", lazy="selectin")

    def __repr__(self):
        return f"<WorkoutSession id={self.id} user_id={self.user_id}>"


class SessionDay(Base):
    __tablename__ = "session_days"
    id = Column(Integer, primary_key=True)
    workout_session_id = Column(Integer, ForeignKey("workout_sessions.id", ondelete="CASCADE"), nullable=False)
    plan_day_name = Column(String(200), nullable=False)
    order = Column(Integer, nullable=False)
    status = Column(PgEnum(SessionStatus), nullable=False, default=SessionStatus.PENDING)

    session = relationship("WorkoutSession", back_populates="session_days", lazy="joined")
    session_exercises = relationship("SessionExercise", back_populates="session_day", cascade="all, delete-orphan",
                                     lazy="selectin")

    def __repr__(self):
        return f"<SessionDay id={self.id} name={self.plan_day_name!r}>"


class SessionExercise(Base):
    __tablename__ = "session_exercises"
    id = Column(Integer, primary_key=True)
    session_day_id = Column(Integer, ForeignKey("session_days.id", ondelete="CASCADE"), nullable=False)
    plan_exercise_name = Column(String(200), nullable=False)
    order = Column(Integer, nullable=False)
    status = Column(PgEnum(SessionStatus), nullable=False, default=SessionStatus.PENDING)

    session_day = relationship("SessionDay", back_populates="session_exercises", lazy="joined")
    session_sets = relationship("SessionSet", back_populates="session_exercise", cascade="all, delete-orphan",
                                lazy="selectin")

    # Relationship to the Exercise model based on plan_exercise_name
    exercise = relationship("Exercise", primaryjoin="SessionExercise.plan_exercise_name == Exercise.name",
                            foreign_keys=[plan_exercise_name], viewonly=True, lazy="joined")

    def __repr__(self):
        return f"<SessionExercise id={self.id} name={self.plan_exercise_name!r}>"


class SessionSet(Base):
    __tablename__ = "session_sets"
    id = Column(Integer, primary_key=True)
    session_exercise_id = Column(Integer, ForeignKey("session_exercises.id", ondelete="CASCADE"), nullable=False)
    order = Column(Integer, nullable=False)
    status = Column(PgEnum(SessionStatus), nullable=False, default=SessionStatus.PENDING)

    # Planned metrics
    plan_reps_min = Column(Integer, nullable=True)
    plan_reps_max = Column(Integer, nullable=True)
    plan_weight = Column(Numeric(6, 2), nullable=True)

    # Actual performance
    reps_done = Column(Integer, nullable=True)
    weight_lifted = Column(Numeric(6, 2), nullable=True)

    session_exercise = relationship("SessionExercise", back_populates="session_sets", lazy="joined")

    def __repr__(self):
        return f"<SessionSet id={self.id} order={self.order}>"


class UserProgress(Base):
    __tablename__ = "user_progress"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    weight = Column(Numeric(5, 2), nullable=True)
    body_measurements = Column(JSONB, nullable=True)
    notes = Column(Text, nullable=True)
    recorded_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=text("now()"), nullable=False)

    user = relationship("User", back_populates="progress_entries", lazy="joined")

    def __repr__(self):
        return f"<UserProgress id={self.id} user_id={self.user_id} recorded_at={self.recorded_at}>"


# --- Таблицы для предпочтений и ограничений ---

restriction_rule_exercises_association = Table(
    'restriction_rule_exercises_association', Base.metadata,
    Column('restriction_rule_id', Integer, ForeignKey('restriction_rules.id', ondelete="CASCADE"), primary_key=True),
    Column('exercise_id', Integer, ForeignKey('exercises.id', ondelete="CASCADE"), primary_key=True)
)


class RestrictionRule(Base):
    __tablename__ = "restriction_rules"
    id = Column(Integer, primary_key=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    restricted_exercises = relationship(
        "Exercise",
        secondary=restriction_rule_exercises_association,
        back_populates="restricted_in_rules",
        lazy="selectin"
    )

    def __repr__(self):
        return f"<RestrictionRule id={self.id} name={self.name!r}>"


class MuscleFocus(Base):
    __tablename__ = "muscle_focuses"
    id = Column(Integer, primary_key=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    muscle_group_id = Column(Integer, ForeignKey("muscle_groups.id", ondelete="CASCADE"), nullable=False)
    priority_modifier = Column(Integer, nullable=False, default=0)  # e.g., +1, -1

    muscle_group = relationship("MuscleGroup", lazy="joined")

    def __repr__(self):
        return f"<MuscleFocus id={self.id} name={self.name!r}>"


user_preferences_restriction_rules_association = Table(
    'user_preferences_restriction_rules', Base.metadata,
    Column('user_preferences_id', Integer, ForeignKey('user_preferences.id', ondelete="CASCADE"), primary_key=True),
    Column('restriction_rule_id', Integer, ForeignKey('restriction_rules.id', ondelete="CASCADE"), primary_key=True)
)

user_preferences_muscle_focuses_association = Table(
    'user_preferences_muscle_focuses', Base.metadata,
    Column('user_preferences_id', Integer, ForeignKey('user_preferences.id', ondelete="CASCADE"), primary_key=True),
    Column('muscle_focus_id', Integer, ForeignKey('muscle_focuses.id', ondelete="CASCADE"), primary_key=True)
)


class UserPreferences(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=text("now()"), nullable=False)

    user = relationship("User", back_populates="preferences", lazy="joined")

    restriction_rules = relationship(
        "RestrictionRule",
        secondary=user_preferences_restriction_rules_association,
        lazy="selectin"
    )
    muscle_focuses = relationship(
        "MuscleFocus",
        secondary=user_preferences_muscle_focuses_association,
        lazy="selectin"
    )

    def __repr__(self):
        return f"<UserPreferences id={self.id} user_id={self.user_id}>"
