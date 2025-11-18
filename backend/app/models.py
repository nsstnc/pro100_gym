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
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.db import Base


# --- Users (с полями профиля) ---
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=True, index=True)
    email = Column(String(255), unique=True, nullable=True)
    username = Column(String(100), nullable=False)

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
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    primary_muscle_group_id = Column(Integer, ForeignKey("muscle_groups.id", ondelete="SET NULL"), nullable=True)
    equipment = Column(String(100), nullable=True)
    is_compound = Column(Boolean, default=True)
    difficulty_level = Column(String(30), nullable=True)
    video_url = Column(String(500), nullable=True)
    image_url = Column(String(500), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=text("now()"), nullable=False)

    primary_muscle_group = relationship("MuscleGroup", back_populates="exercises", lazy="joined")

    def __repr__(self):
        return f"<Exercise id={self.id} name={self.name!r}>"


class WorkoutPlan(Base):
    __tablename__ = "workout_plans"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(200), nullable=False)
    split_type = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
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

    # exercises: JSONB array with performed exercises and sets details
    exercises = Column(JSONB, nullable=False, server_default="[]")

    created_at = Column(DateTime(timezone=True), server_default=text("now()"), nullable=False)

    user = relationship("User", back_populates="workout_sessions", lazy="joined")
    workout_plan = relationship("WorkoutPlan", lazy="joined")

    def __repr__(self):
        return f"<WorkoutSession id={self.id} user_id={self.user_id}>"


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


class UserPreferences(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    # muscle_preferences: list of {"muscle_group_id": int, "preference":"like|neutral|dislike"}
    muscle_preferences = Column(JSONB, nullable=False, server_default="[]")
    # restrictions: list of {"type":"knee_pain", "severity":"medium", "notes": "..."}
    restrictions = Column(JSONB, nullable=False, server_default="[]")

    created_at = Column(DateTime(timezone=True), server_default=text("now()"), nullable=False)

    user = relationship("User", back_populates="preferences", lazy="joined")

    def __repr__(self):
        return f"<UserPreferences id={self.id} user_id={self.user_id}>"
