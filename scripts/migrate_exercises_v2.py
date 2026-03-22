"""
Миграция тренировочной программы на v2.0

Что делает:
1. Добавляет колонку 'notes' в таблицу exercises (если нет)
2. Деактивирует старые упражнения (is_active=False)
3. Добавляет новые упражнения из seed.py
4. Обновляет фазу "Знакомство" → "Повторное знакомство" (sets_modifier 0.5→0.6)
5. Создаёт CurrentWeight записи для новых упражнений

Запуск:
    ssh bot "cd ~/Artur/Skuper && docker compose exec budget_bot python scripts/migrate_exercises_v2.py"
или локально:
    cd F:/budget_bot && ./venv/Scripts/python.exe scripts/migrate_exercises_v2.py
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from db.database import engine, async_session
from db.models import Exercise, CurrentWeight, Phase
from db.seed import INITIAL_EXERCISES, INITIAL_PHASES
from sqlalchemy import select


async def migrate():
    async with engine.begin() as conn:
        # 1. Добавить колонку notes если нет
        result = await conn.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='exercises' AND column_name='notes'"
        ))
        if not result.fetchone():
            await conn.execute(text("ALTER TABLE exercises ADD COLUMN notes TEXT"))
            print("✅ Добавлена колонка 'notes' в exercises")
        else:
            print("ℹ️ Колонка 'notes' уже существует")

    async with async_session() as session:
        # 2. Деактивировать все старые упражнения
        await session.execute(
            text("UPDATE exercises SET is_active = false")
        )
        print("✅ Старые упражнения деактивированы")

        # 3. Добавить/обновить упражнения из нового набора
        new_ids = [e["exercise_id"] for e in INITIAL_EXERCISES]

        for data in INITIAL_EXERCISES:
            # Проверяем, существует ли упражнение
            result = await session.execute(
                select(Exercise).where(Exercise.exercise_id == data["exercise_id"])
            )
            existing = result.scalar_one_or_none()

            if existing:
                # Обновляем существующее
                existing.name = data["name"]
                existing.day = data["day"]
                existing.order = data["order"]
                existing.category = data.get("category", "")
                existing.weight_step = data["weight_step"]
                existing.reps_min = data["reps_min"]
                existing.reps_max = data["reps_max"]
                existing.rest_seconds = data["rest_seconds"]
                existing.default_sets = data["default_sets"]
                existing.notes = data.get("notes", "")
                existing.is_active = True
                print(f"  🔄 Обновлено: {data['exercise_id']} ({data['name']})")
            else:
                # Создаём новое
                exercise = Exercise(
                    exercise_id=data["exercise_id"],
                    name=data["name"],
                    day=data["day"],
                    order=data["order"],
                    category=data.get("category", ""),
                    weight_step=data["weight_step"],
                    reps_min=data["reps_min"],
                    reps_max=data["reps_max"],
                    rest_seconds=data["rest_seconds"],
                    default_sets=data["default_sets"],
                    notes=data.get("notes", ""),
                    is_active=True,
                )
                session.add(exercise)
                print(f"  ➕ Добавлено: {data['exercise_id']} ({data['name']})")

        await session.flush()

        # 4. Создать CurrentWeight для новых упражнений (если нет)
        for data in INITIAL_EXERCISES:
            result = await session.execute(
                select(CurrentWeight).where(CurrentWeight.exercise_id == data["exercise_id"])
            )
            if not result.scalar_one_or_none():
                cw = CurrentWeight(
                    exercise_id=data["exercise_id"],
                    weight=0.0,
                    target_reps=f"{data['reps_min']}-{data['reps_max']}",
                    status="in_progress",
                )
                session.add(cw)
                print(f"  📊 CurrentWeight создан: {data['exercise_id']}")

        # 5. Обновить фазу "Знакомство" → "Повторное знакомство"
        result = await session.execute(
            select(Phase).where(Phase.name == "Знакомство")
        )
        phase = result.scalar_one_or_none()
        if phase:
            phase.name = "Повторное знакомство"
            phase.sets_modifier = 0.6
            print("✅ Фаза 'Знакомство' → 'Повторное знакомство' (sets_modifier=0.6)")

        await session.commit()

    print("\n🎉 Миграция v2.0 завершена!")
    print(f"   Упражнений в программе: {len(INITIAL_EXERCISES)}")
    print(f"   День A: {len([e for e in INITIAL_EXERCISES if e['day'] == 'A'])} упражнений")
    print(f"   День B: {len([e for e in INITIAL_EXERCISES if e['day'] == 'B'])} упражнений")


if __name__ == "__main__":
    asyncio.run(migrate())
