"""SQLAlchemy ORM models for Budget Bot (PostgreSQL)."""

from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import (
    BigInteger, Boolean, Date, DateTime, Float, ForeignKey,
    Integer, JSON, String, Text, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base


# ============================================
# ФИНАНСЫ
# ============================================

class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    currency: Mapped[str] = mapped_column(String(10), default="BYN")
    balance: Mapped[float] = mapped_column(Float, default=0.0)
    initial_balance: Mapped[float] = mapped_column(Float, default=0.0)
    emoji: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    transactions_from: Mapped[List["Transaction"]] = relationship(
        "Transaction", foreign_keys="Transaction.account_id", back_populates="account"
    )
    transactions_to: Mapped[List["Transaction"]] = relationship(
        "Transaction", foreign_keys="Transaction.to_account_id", back_populates="to_account"
    )


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    type: Mapped[str] = mapped_column(String(20))  # Доход / Расход
    emoji: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    budget_limit: Mapped[float] = mapped_column(Float, default=0.0)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    transactions: Mapped[List["Transaction"]] = relationship(back_populates="category")


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    type: Mapped[str] = mapped_column(String(30))  # Доход / Расход / Перевод / Обмен валюты
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id"), nullable=True)
    amount: Mapped[float] = mapped_column(Float)
    to_account_id: Mapped[Optional[int]] = mapped_column(ForeignKey("accounts.id"), nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    exchange_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    amount_to: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="BYN")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    # Флаг синхронизации с Google Sheets (для экспорта)
    synced_to_sheets: Mapped[bool] = mapped_column(Boolean, default=False)

    account: Mapped["Account"] = relationship(
        "Account", foreign_keys=[account_id], back_populates="transactions_from"
    )
    to_account: Mapped[Optional["Account"]] = relationship(
        "Account", foreign_keys=[to_account_id], back_populates="transactions_to"
    )
    category: Mapped[Optional["Category"]] = relationship(back_populates="transactions")


# ============================================
# ТРЕНИРОВКИ
# ============================================

class Exercise(Base):
    __tablename__ = "exercises"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    exercise_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    day: Mapped[str] = mapped_column(String(5))   # A / B
    order: Mapped[int] = mapped_column(Integer, default=0)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    weight_step: Mapped[float] = mapped_column(Float, default=2.5)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    current_weight: Mapped[Optional["CurrentWeight"]] = relationship(
        back_populates="exercise", uselist=False
    )
    sets: Mapped[List["WorkoutSet"]] = relationship(back_populates="exercise")


class Phase(Base):
    __tablename__ = "phases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    weeks: Mapped[str] = mapped_column(String(20))   # "1-2", "3-4" и т.д.
    rpe_min: Mapped[int] = mapped_column(Integer)
    rpe_max: Mapped[int] = mapped_column(Integer)
    sets_modifier: Mapped[float] = mapped_column(Float, default=1.0)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class Workout(Base):
    __tablename__ = "workouts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    day_type: Mapped[str] = mapped_column(String(5))  # A / B
    week: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    phase: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    energy_before: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    energy_after: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sleep_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sleep_quality: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    back_pain: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    emotional_wave: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    synced_to_sheets: Mapped[bool] = mapped_column(Boolean, default=False)

    sets: Mapped[List["WorkoutSet"]] = relationship(back_populates="workout")


class WorkoutSet(Base):
    __tablename__ = "workout_sets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workout_id: Mapped[int] = mapped_column(ForeignKey("workouts.id"))
    exercise_id: Mapped[str] = mapped_column(String(50), index=True)
    set_number: Mapped[int] = mapped_column(Integer)
    weight: Mapped[float] = mapped_column(Float)
    reps: Mapped[int] = mapped_column(Integer)
    rpe: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    workout: Mapped["Workout"] = relationship(back_populates="sets")
    exercise: Mapped[Optional["Exercise"]] = relationship(
        "Exercise", foreign_keys=[exercise_id],
        primaryjoin="WorkoutSet.exercise_id == Exercise.exercise_id",
        back_populates="sets"
    )


class CurrentWeight(Base):
    __tablename__ = "current_weights"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    exercise_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("exercises.exercise_id"), unique=True, index=True
    )
    weight: Mapped[float] = mapped_column(Float, default=0.0)
    target_reps: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    last_sets: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # список последних RPE
    status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # ready / in_progress
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    exercise: Mapped["Exercise"] = relationship(back_populates="current_weight")


# ============================================
# СИНХРОНИЗАЦИЯ С GOOGLE SHEETS
# ============================================

class SheetsSyncLog(Base):
    __tablename__ = "sheets_sync_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sync_type: Mapped[str] = mapped_column(String(50))  # finance / workout / full
    status: Mapped[str] = mapped_column(String(20))      # success / error
    records_synced: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
