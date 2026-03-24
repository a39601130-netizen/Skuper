"""
Сервис бэкапа PostgreSQL → Google Sheets
Экспортирует транзакции и тренировки за указанный месяц
"""
import logging
import asyncio
from datetime import date
from typing import Dict, Any, Optional

from sqlalchemy import select, extract, update
from sqlalchemy.orm import selectinload

import config
from db.database import async_session
from db.models import (
    Transaction, Workout, WorkoutSet,
    CurrentWeight, SheetsSyncLog
)
from services.sheets import BaseSheetsService

logger = logging.getLogger(__name__)


class BackupService:
    """Экспорт данных из PostgreSQL в Google Sheets"""

    def __init__(self):
        self.finance_sheets = BaseSheetsService(config.GOOGLE_SHEETS_FINANCE_ID)
        self.workout_sheets = BaseSheetsService(config.GOOGLE_SHEETS_WORKOUT_ID)

    def _clear_data_rows(self, service: BaseSheetsService, sheet_name: str, header_rows: int = 3):
        """Очистить данные на листе, оставив заголовки"""
        sheet = service.get_sheet(sheet_name)
        all_values = sheet.get_all_values()
        total_rows = len(all_values)
        if total_rows > header_rows:
            sheet.delete_rows(header_rows + 1, total_rows)

    async def backup_finances(self, year: int, month: int) -> Dict[str, Any]:
        """
        Экспорт транзакций за месяц в Google Sheets

        Returns:
            Dict с результатами: count, errors
        """
        # 1. Читаем транзакции из PG
        async with async_session() as db:
            result = await db.execute(
                select(Transaction)
                .options(
                    selectinload(Transaction.account),
                    selectinload(Transaction.to_account),
                    selectinload(Transaction.category)
                )
                .where(
                    extract('year', Transaction.date) == year,
                    extract('month', Transaction.date) == month
                )
                .order_by(Transaction.date, Transaction.id)
            )
            transactions = result.scalars().all()

        if not transactions:
            return {"count": 0, "errors": []}

        # 2. Очищаем лист транзакций (оставляем строки 1-3: настройки + заголовки)
        await asyncio.to_thread(
            self._clear_data_rows, self.finance_sheets, config.SHEET_TRANSACTIONS, 3
        )

        # 3. Обновляем месяц/год в настройках (C1 = месяц, E1 = год)
        def update_settings():
            sheet = self.finance_sheets.get_sheet(config.SHEET_TRANSACTIONS)
            sheet.update_cell(1, 3, month)
            sheet.update_cell(1, 5, year)
        await asyncio.to_thread(update_settings)

        # 4. Формируем строки и пишем пакетно
        rows = []
        for t in transactions:
            account_name = t.account.name if t.account else ""
            to_account_name = t.to_account.name if t.to_account else ""
            category_name = t.category.name if t.category else ""

            full_date = t.date.strftime("%d.%m.%Y")
            hours_rate = round(t.hours * config.BASE_HOURLY_RATE, 2) if t.hours else ""

            row = [
                t.date.day,                             # A: День
                t.type,                                 # B: Тип
                account_name,                           # C: Счёт
                category_name,                          # D: Категория
                t.amount,                               # E: Сумма
                to_account_name,                        # F: Счёт Куда
                t.comment or "",                        # G: Комментарий
                full_date,                              # H: Полная дата
                t.hours if t.hours else "",             # I: Часы
                hours_rate,                             # J: Часы×6.5
                t.exchange_rate if t.exchange_rate else "",  # K: Курс
                t.amount_to if t.amount_to else "",     # L: Сумма зачисления
                t.currency                              # M: Валюта
            ]
            rows.append(row)

        # Пакетная запись (append_rows быстрее чем по одной)
        errors = []
        try:
            def write_rows():
                sheet = self.finance_sheets.get_sheet(config.SHEET_TRANSACTIONS)
                sheet.append_rows(rows, value_input_option='USER_ENTERED')
            await asyncio.to_thread(write_rows)
        except Exception as e:
            logger.error(f"Ошибка записи транзакций в Sheets: {e}")
            errors.append(f"Транзакции: {e}")

        # 5. Помечаем как синхронизированные
        if not errors:
            async with async_session() as db:
                tx_ids = [t.id for t in transactions]
                await db.execute(
                    update(Transaction)
                    .where(Transaction.id.in_(tx_ids))
                    .values(synced_to_sheets=True)
                )
                await db.commit()

        return {"count": len(transactions), "errors": errors}

    async def backup_workouts(self, year: int, month: int) -> Dict[str, Any]:
        """
        Экспорт тренировок + подходов за месяц в Google Sheets

        Returns:
            Dict с результатами: workouts_count, sets_count, errors
        """
        # 1. Читаем тренировки из PG
        async with async_session() as db:
            result = await db.execute(
                select(Workout)
                .options(selectinload(Workout.sets))
                .where(
                    extract('year', Workout.date) == year,
                    extract('month', Workout.date) == month
                )
                .order_by(Workout.date)
            )
            workouts = result.scalars().all()

        if not workouts:
            return {"workouts_count": 0, "sets_count": 0, "errors": []}

        errors = []

        # 2. Очищаем листы Тренировки и Подходы (оставляем строку 1 — заголовки)
        await asyncio.to_thread(
            self._clear_data_rows, self.workout_sheets, config.SHEET_WORKOUTS, 1
        )
        await asyncio.to_thread(
            self._clear_data_rows, self.workout_sheets, config.SHEET_SETS, 2  # 2 строки: заголовки + подсказки
        )

        # 3. Записываем тренировки
        workout_rows = []
        for w in workouts:
            workout_rows.append([
                w.id,                                    # workout_id
                str(w.date),                             # date
                w.day_type,                              # day_type
                w.week or "",                            # week_num
                w.phase or "",                           # phase
                "",                                      # started_at
                "",                                      # finished_at
                "",                                      # duration_min
                w.energy_before if w.energy_before is not None else "",
                w.energy_after if w.energy_after is not None else "",
                w.emotional_wave or "",                  # emotional_wave
                w.sleep_hours if w.sleep_hours is not None else "",
                w.sleep_quality if w.sleep_quality is not None else "",
                w.back_pain if w.back_pain is not None else "",
                "",                                      # warmup_done
                "",                                      # mcgill_done
                w.notes or ""                            # notes
            ])

        try:
            def write_workouts():
                sheet = self.workout_sheets.get_sheet(config.SHEET_WORKOUTS)
                sheet.append_rows(workout_rows, value_input_option='USER_ENTERED')
            await asyncio.to_thread(write_workouts)
        except Exception as e:
            logger.error(f"Ошибка записи тренировок в Sheets: {e}")
            errors.append(f"Тренировки: {e}")

        # 4. Записываем подходы
        all_sets = []
        for w in workouts:
            for s in sorted(w.sets, key=lambda x: (x.exercise_id, x.set_number)):
                all_sets.append([
                    s.id,                # set_id
                    s.workout_id,        # workout_id
                    s.exercise_id,       # exercise_id
                    s.set_number,        # set_num
                    s.weight,            # weight
                    s.reps,              # reps
                    s.rpe if s.rpe is not None else "",  # rpe
                    "",                  # tempo
                    s.notes or "",       # notes
                    ""                   # created_at
                ])

        if all_sets:
            try:
                def write_sets():
                    sheet = self.workout_sheets.get_sheet(config.SHEET_SETS)
                    sheet.append_rows(all_sets, value_input_option='USER_ENTERED')
                await asyncio.to_thread(write_sets)
            except Exception as e:
                logger.error(f"Ошибка записи подходов в Sheets: {e}")
                errors.append(f"Подходы: {e}")

        # 5. Помечаем как синхронизированные
        if not errors:
            async with async_session() as db:
                w_ids = [w.id for w in workouts]
                await db.execute(
                    update(Workout)
                    .where(Workout.id.in_(w_ids))
                    .values(synced_to_sheets=True)
                )
                await db.commit()

        return {
            "workouts_count": len(workouts),
            "sets_count": len(all_sets),
            "errors": errors
        }

    async def backup_current_weights(self) -> Dict[str, Any]:
        """Экспорт текущих весов в Google Sheets"""
        async with async_session() as db:
            result = await db.execute(
                select(CurrentWeight)
                .options(selectinload(CurrentWeight.exercise))
            )
            weights = result.scalars().all()

        if not weights:
            return {"count": 0, "errors": []}

        # Очищаем лист (оставляем заголовки)
        await asyncio.to_thread(
            self._clear_data_rows, self.workout_sheets, config.SHEET_CURRENT_WEIGHTS, 1
        )

        rows = []
        for cw in weights:
            exercise = cw.exercise
            exercise_name = exercise.name if exercise else ""
            reps_min = exercise.reps_min if exercise else ""
            reps_max = exercise.reps_max if exercise else ""
            last_sets = cw.last_sets or []
            rows.append([
                cw.exercise_id,                          # exercise_id
                exercise_name,                           # name
                cw.weight,                               # current_weight
                reps_min,                                # target_reps_min
                reps_max,                                # target_reps_max
                last_sets[0] if len(last_sets) > 0 else "",
                last_sets[1] if len(last_sets) > 1 else "",
                last_sets[2] if len(last_sets) > 2 else "",
                last_sets[3] if len(last_sets) > 3 else "",
                "",                                      # all_at_max
                "",                                      # ready_for_increase
                ""                                       # next_weight
            ])

        errors = []
        try:
            def write_weights():
                sheet = self.workout_sheets.get_sheet(config.SHEET_CURRENT_WEIGHTS)
                sheet.append_rows(rows, value_input_option='USER_ENTERED')
            await asyncio.to_thread(write_weights)
        except Exception as e:
            logger.error(f"Ошибка записи весов в Sheets: {e}")
            errors.append(f"Веса: {e}")

        return {"count": len(weights), "errors": errors}

    async def full_backup(self, year: int, month: int) -> Dict[str, Any]:
        """
        Полный бэкап: транзакции + тренировки + веса

        Returns:
            Dict со сводкой
        """
        results = {}

        # Финансы
        results["finance"] = await self.backup_finances(year, month)

        # Тренировки
        results["workouts"] = await self.backup_workouts(year, month)

        # Текущие веса (не зависят от месяца)
        results["weights"] = await self.backup_current_weights()

        # Логируем результат
        total_errors = (
            results["finance"]["errors"]
            + results["workouts"]["errors"]
            + results["weights"]["errors"]
        )
        status = "error" if total_errors else "success"
        total_records = (
            results["finance"]["count"]
            + results["workouts"]["workouts_count"]
            + results["workouts"]["sets_count"]
            + results["weights"]["count"]
        )

        async with async_session() as db:
            log = SheetsSyncLog(
                sync_type="full",
                status=status,
                records_synced=total_records,
                error_message="; ".join(str(e) for e in total_errors) if total_errors else None
            )
            db.add(log)
            await db.commit()

        results["status"] = status
        results["total_records"] = total_records
        return results
