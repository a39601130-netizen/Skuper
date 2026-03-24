"""
Одноразовый скрипт миграции данных из Google Sheets → PostgreSQL.

Запуск:
    python scripts/migrate_sheets_to_pg.py

Что мигрирует:
    - Счета (Sheets → accounts)
    - Категории (Sheets → categories + budget_limit)
    - Транзакции (Sheets → transactions, ~все строки)
    - Упражнения (Sheets → exercises)
    - Текущие веса (Sheets → current_weights)
    - Тренировки (Sheets → workouts)
    - Подходы (Sheets → workout_sets)
"""

import asyncio
import logging
import sys
import os

# Добавляем корень проекта в sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, date
from typing import Optional

from sqlalchemy import select

import config
from db.database import init_db, async_session
from db.models import Account, Category, Transaction, Exercise, Workout, WorkoutSet, CurrentWeight, Phase
from db.seed import seed_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def safe_float(value, default=0.0) -> float:
    if value is None or value == "" or value == "-":
        return default
    try:
        return float(str(value).strip().replace("\u00A0", "").replace(" ", "").replace(",", "."))
    except (ValueError, TypeError):
        return default


def safe_int(value, default=0) -> int:
    return int(safe_float(value, default))


def parse_date(day_val, month: int, year: int) -> Optional[date]:
    try:
        day = int(safe_float(day_val))
        if 1 <= day <= 31:
            return date(year, month, day)
    except Exception:
        pass
    return None


async def migrate_accounts(sheets_service, session):
    logger.info("📋 Migrating accounts...")
    accounts_data = sheets_service.get_accounts_balance()

    # Очищаем существующие
    for a in (await session.execute(select(Account))).scalars().all():
        await session.delete(a)
    await session.flush()

    for i, acc in enumerate(accounts_data):
        name = acc.get("name", "")
        if not name:
            continue
        account = Account(
            name=name,
            currency=acc.get("currency", "BYN"),
            balance=safe_float(acc.get("current", 0)),
            initial_balance=safe_float(acc.get("initial", 0)),
            emoji=config.CATEGORY_EMOJI.get(name, "💳"),
            sort_order=i + 1,
        )
        session.add(account)

    await session.commit()
    logger.info(f"  ✅ {len(accounts_data)} accounts migrated")


async def migrate_categories(sheets_service, session):
    logger.info("📋 Migrating categories...")
    cats_data = sheets_service.get_categories_budget()

    for j in (await session.execute(select(Category))).scalars().all():
        await session.delete(j)
    await session.flush()

    for i, cat in enumerate(cats_data):
        name = cat.get("name", "")
        if not name:
            continue
        category = Category(
            name=name,
            type=cat.get("type", "Расход"),
            emoji=config.CATEGORY_EMOJI.get(name, "📦"),
            budget_limit=safe_float(cat.get("budget", 0)),
            sort_order=i + 1,
        )
        session.add(category)

    await session.commit()
    logger.info(f"  ✅ {len(cats_data)} categories migrated")


async def migrate_transactions(sheets_service, session):
    logger.info("📋 Migrating transactions...")

    # Получаем маппинг accounts и categories
    acc_map = {a.name: a for a in (await session.execute(select(Account))).scalars().all()}
    cat_map = {}
    for c in (await session.execute(select(Category))).scalars().all():
        cat_map[(c.name, c.type)] = c

    period = sheets_service.get_current_month_settings()
    month = period["month"]
    year = period["year"]

    import gspread
    from google.oauth2.service_account import Credentials
    scopes = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_file(config.GOOGLE_CREDENTIALS_FILE, scopes=scopes)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(config.GOOGLE_SHEETS_FINANCE_ID)
    sheet = spreadsheet.worksheet(config.SHEET_TRANSACTIONS)
    data = sheet.get_all_values()

    count = 0
    for row in data[3:]:  # Пропускаем заголовки и настройки
        if not row[0] or not row[0].strip():
            continue
        try:
            tx_date = parse_date(row[0], month, year)
            if not tx_date:
                continue

            trans_type = row[1].strip() if len(row) > 1 and row[1] else ""
            account_name = row[2].strip() if len(row) > 2 and row[2] else ""
            category_name = row[3].strip() if len(row) > 3 and row[3] else ""
            amount = safe_float(row[4]) if len(row) > 4 else 0
            to_account_name = row[5].strip() if len(row) > 5 and row[5] else ""
            comment = row[6].strip() if len(row) > 6 and row[6] else ""
            hours = safe_float(row[8]) if len(row) > 8 and row[8] else None
            exchange_rate = safe_float(row[10]) if len(row) > 10 and row[10] else None
            amount_to = safe_float(row[11]) if len(row) > 11 and row[11] else None
            currency = row[12].strip() if len(row) > 12 and row[12] else "BYN"

            if not account_name or amount == 0:
                continue

            account = acc_map.get(account_name)
            if not account:
                # Создаём новый счёт
                account = Account(name=account_name, currency="BYN", sort_order=99)
                session.add(account)
                await session.flush()
                acc_map[account_name] = account

            # Категория
            category_id = None
            if category_name:
                cat_type = "Доход" if trans_type == "Доход" else "Расход"
                cat = cat_map.get((category_name, cat_type))
                if cat:
                    category_id = cat.id

            to_account_id = None
            if to_account_name:
                to_acc = acc_map.get(to_account_name)
                if to_acc:
                    to_account_id = to_acc.id

            tx = Transaction(
                date=tx_date,
                type=trans_type,
                account_id=account.id,
                category_id=category_id,
                amount=amount,
                to_account_id=to_account_id,
                comment=comment or None,
                hours=hours if hours and hours > 0 else None,
                exchange_rate=exchange_rate if exchange_rate and exchange_rate > 0 else None,
                amount_to=amount_to if amount_to and amount_to > 0 else None,
                currency=currency,
                synced_to_sheets=True,  # Эти данные пришли из Sheets
            )
            session.add(tx)
            count += 1

        except Exception as e:
            logger.warning(f"  ⚠️  Skipping row {row[:5]}: {e}")
            continue

    await session.commit()
    logger.info(f"  ✅ {count} transactions migrated")


async def migrate_exercises(workout_service, session):
    logger.info("📋 Migrating exercises...")
    exercises_data = workout_service.get_exercises()

    for e in (await session.execute(select(Exercise))).scalars().all():
        await session.delete(e)
    await session.flush()

    for ex in exercises_data:
        eid = ex.get("exercise_id", "")
        if not eid:
            continue
        exercise = Exercise(
            exercise_id=eid,
            name=ex.get("name", eid),
            day=ex.get("day", "A"),
            order=safe_int(ex.get("order", 0)),
            category=ex.get("category", ""),
            weight_step=safe_float(ex.get("weight_step", 2.5)),
        )
        session.add(exercise)

    await session.commit()
    logger.info(f"  ✅ {len(exercises_data)} exercises migrated")


async def migrate_current_weights(workout_service, session):
    logger.info("📋 Migrating current weights...")
    weights_data = workout_service.get_current_weights()

    for w in (await session.execute(select(CurrentWeight))).scalars().all():
        await session.delete(w)
    await session.flush()

    count = 0
    for eid, w in weights_data.items():
        # Проверяем что упражнение существует
        ex_result = await session.execute(select(Exercise).where(Exercise.exercise_id == eid))
        ex = ex_result.scalar_one_or_none()
        if not ex:
            continue

        cw = CurrentWeight(
            exercise_id=eid,
            weight=safe_float(w.get("current_weight", 0)),
            target_reps=str(w.get("target_reps", "")) or None,
            status=w.get("status", "") or None,
        )
        session.add(cw)
        count += 1

    await session.commit()
    logger.info(f"  ✅ {count} current weights migrated")


async def migrate_workouts(workout_service, session):
    logger.info("📋 Migrating workout history...")
    history = workout_service.get_workout_history(limit=100)

    for w in (await session.execute(select(Workout))).scalars().all():
        await session.delete(w)
    await session.flush()

    count = 0
    for wdata in reversed(history):  # От старых к новым
        try:
            date_str = wdata.get("date", "")
            if not date_str:
                continue
            try:
                workout_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                try:
                    workout_date = datetime.strptime(date_str, "%d.%m.%Y").date()
                except ValueError:
                    continue

            workout = Workout(
                date=workout_date,
                day_type=wdata.get("day_type", "A"),
                week=safe_int(wdata.get("week")) if wdata.get("week") else None,
                phase=wdata.get("phase", "") or None,
                energy_before=safe_int(wdata.get("energy_before")) if wdata.get("energy_before") else None,
                energy_after=safe_int(wdata.get("energy_after")) if wdata.get("energy_after") else None,
                sleep_hours=safe_float(wdata.get("sleep_hours")) if wdata.get("sleep_hours") else None,
                sleep_quality=safe_int(wdata.get("sleep_quality")) if wdata.get("sleep_quality") else None,
                back_pain=safe_int(wdata.get("back_pain")) if wdata.get("back_pain") else None,
                emotional_wave=wdata.get("emotional_wave", "") or None,
                notes=wdata.get("notes", "") or None,
                synced_to_sheets=True,
            )
            session.add(workout)
            count += 1
        except Exception as e:
            logger.warning(f"  ⚠️  Skipping workout {wdata.get('date')}: {e}")

    await session.commit()
    logger.info(f"  ✅ {count} workouts migrated")


async def main():
    logger.info("🚀 Starting migration: Google Sheets → PostgreSQL")
    logger.info(f"   DB: {config.DATABASE_URL}")
    logger.info(f"   Finance Sheet: {config.GOOGLE_SHEETS_FINANCE_ID}")
    logger.info(f"   Workout Sheet: {config.GOOGLE_SHEETS_WORKOUT_ID}")

    # Инициализируем БД
    await init_db()
    await seed_db()

    # Подключаемся к Google Sheets
    from services.sheets import get_sheets_service
    from services.workout_sheets import get_workout_service

    try:
        sheets = get_sheets_service()
        logger.info("✅ Finance Google Sheets connected")
    except Exception as e:
        logger.error(f"❌ Finance Google Sheets error: {e}")
        return

    try:
        workout_svc = get_workout_service()
        logger.info("✅ Workout Google Sheets connected")
    except Exception as e:
        logger.warning(f"⚠️  Workout Google Sheets error: {e}. Skipping workout migration.")
        workout_svc = None

    async with async_session() as session:
        await migrate_accounts(sheets, session)
        await migrate_categories(sheets, session)
        await migrate_transactions(sheets, session)

        if workout_svc:
            await migrate_exercises(workout_svc, session)
            await migrate_current_weights(workout_svc, session)
            await migrate_workouts(workout_svc, session)

    logger.info("✅ Migration completed successfully!")
    logger.info("💡 Теперь запусти: python run.py")


if __name__ == "__main__":
    asyncio.run(main())
