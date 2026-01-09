"""
Сервис для работы с Google Sheets
"""
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from typing import Optional, Dict, List, Any
import config


def safe_float(value, default=0.0) -> float:
    """
    Безопасное преобразование строки в float.
    Обрабатывает европейский формат с запятой (140,82)
    """
    if value is None or value == "" or value == "-":
        return default
    
    if isinstance(value, (int, float)):
        return float(value)
    
    try:
        # Убираем пробелы и заменяем запятую на точку
        cleaned = str(value).strip().replace(" ", "").replace(",", ".")
        return float(cleaned)
    except (ValueError, TypeError):
        return default


def safe_int(value, default=0) -> int:
    """Безопасное преобразование в int"""
    if value is None or value == "":
        return default
    
    try:
        # Сначала преобразуем в float (на случай "1,0"), потом в int
        return int(safe_float(value, default))
    except (ValueError, TypeError):
        return default

class GoogleSheetsService:
    """Сервис для работы с Google Sheets таблицей бюджета"""
    
    def __init__(self):
        self.client = None
        self.spreadsheet = None
        self._connect()
    
    def _connect(self):
        """Подключение к Google Sheets"""
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            config.GOOGLE_CREDENTIALS_FILE, scope
        )
        self.client = gspread.authorize(creds)
        self.spreadsheet = self.client.open_by_key(config.GOOGLE_SHEETS_ID)
    
    def get_references(self) -> Dict[str, List[str]]:
        """Получить справочники (типы, счета, категории)"""
        sheet = self.spreadsheet.worksheet(config.SHEET_REFERENCES)
        data = sheet.get_all_values()
        
        # Парсим данные начиная с 4-й строки (индекс 3)
        types = []
        accounts = []
        categories = []
        
        for row in data[3:]:  # Пропускаем заголовки
            if row[0] and row[0].strip():
                types.append(row[0].strip())
            if row[1] and row[1].strip():
                accounts.append(row[1].strip())
            if row[2] and row[2].strip():
                categories.append(row[2].strip())
        
        return {
            "types": types,
            "accounts": accounts,
            "categories": categories
        }
    
    def get_accounts_balance(self) -> List[Dict[str, Any]]:
        """Получить балансы всех счетов"""
        sheet = self.spreadsheet.worksheet(config.SHEET_ACCOUNTS)
        data = sheet.get_all_values()
        
        accounts = []
        for row in data[3:]:  # Пропускаем заголовки
            if row[0] and row[0].strip():
                accounts.append({
                    "name": row[0].strip(),
                    "initial": safe_float(row[1]) if row[1] else 0,
                    "current": safe_float(row[2]) if row[2] else 0,
                    "currency": row[3] if len(row) > 3 and row[3] else "BYN"
                })
        
        return accounts
    
    def get_categories_budget(self) -> List[Dict[str, Any]]:
        """Получить бюджеты и расходы по категориям"""
        sheet = self.spreadsheet.worksheet(config.SHEET_CATEGORIES)
        data = sheet.get_all_values()
        
        categories = []
        for row in data[1:]:  # Пропускаем заголовок
            if row[1] and row[1].strip():
                categories.append({
                    "type": row[0].strip(),
                    "name": row[1].strip(),
                    "budget": safe_float(row[2]) if row[2] else 0,
                    "spent": safe_float(row[3]) if row[3] else 0,
                    "remaining": safe_float(row[4]) if row[4] else 0,
                    "progress": safe_float(row[5]) if row[5] else 0
                })
        
        return categories
    
    def get_current_month_settings(self) -> Dict[str, int]:
        """Получить текущий месяц и год из настроек таблицы"""
        sheet = self.spreadsheet.worksheet(config.SHEET_TRANSACTIONS)
        data = sheet.get_all_values()
        
        # Настройки в первой строке: C1 = месяц, E1 = год
        month = safe_int(data[0][2], datetime.now().month)
        year = safe_int(data[0][4], datetime.now().year)
        
        return {"month": month, "year": year}
    
    def add_transaction(
        self,
        day: int,
        trans_type: str,
        account: str,
        category: Optional[str],
        amount: float,
        to_account: Optional[str] = None,
        comment: Optional[str] = None,
        hours: Optional[float] = None
    ) -> bool:
        """
        Добавить транзакцию в таблицу
        
        Args:
            day: День месяца (1-31)
            trans_type: Тип (Доход, Расход, Перевод)
            account: Счёт списания
            category: Категория (для Доходов и Расходов)
            amount: Сумма
            to_account: Счёт зачисления (для Переводов)
            comment: Комментарий
            hours: Количество часов (для расчета зарплаты)
        
        Returns:
            bool: Успех операции
        """
        try:
            sheet = self.spreadsheet.worksheet(config.SHEET_TRANSACTIONS)
            
            # Формируем строку данных
            # A: Дата, B: Тип, C: Счёт, D: Категория, E: Сумма, 
            # F: Счёт Куда, G: Комментарий, H: (формула), I: Часы
            row_data = [
                day,                           # A: Дата (день)
                trans_type,                    # B: Тип
                account,                       # C: Счёт
                category or "",                # D: Категория
                amount,                        # E: Сумма
                to_account or "",              # F: Счёт Куда
                comment or "",                 # G: Комментарий
                "",                            # H: Полная дата (формула в таблице)
                hours if hours else "",        # I: Часы
                ""                             # J: Часы×6.5 (формула)
            ]
            
            # Добавляем в конец таблицы
            sheet.append_row(row_data, value_input_option='USER_ENTERED')
            
            return True
            
        except Exception as e:
            print(f"Ошибка записи в Google Sheets: {e}")
            return False
    
    def get_monthly_summary(self) -> Dict[str, Any]:
        """Получить сводку за текущий месяц"""
        categories = self.get_categories_budget()
        accounts = self.get_accounts_balance()
        
        total_income = sum(c["spent"] for c in categories if c["type"] == "Доход")
        total_expense = sum(c["spent"] for c in categories if c["type"] == "Расход")
        total_balance = sum(a["current"] for a in accounts if a["currency"] == "BYN")
        
        # Категории с превышением бюджета
        over_budget = [
            c for c in categories 
            if c["type"] == "Расход" and c["budget"] > 0 and c["spent"] > c["budget"]
        ]
        
        # Категории близкие к лимиту (>80%)
        near_limit = [
            c for c in categories 
            if c["type"] == "Расход" and c["budget"] > 0 
            and c["progress"] >= 0.8 and c["progress"] < 1
        ]
        
        return {
            "total_income": total_income,
            "total_expense": total_expense,
            "balance": total_income - total_expense,
            "total_on_accounts": total_balance,
            "accounts": accounts,
            "categories": categories,
            "over_budget": over_budget,
            "near_limit": near_limit
        }
    
    def get_recent_transactions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Получить последние транзакции"""
        sheet = self.spreadsheet.worksheet(config.SHEET_TRANSACTIONS)
        data = sheet.get_all_values()

        transactions = []
        for row in data[3:]:  # Пропускаем настройки и заголовки
            if row[0] and row[0].strip():
                transactions.append({
                    "day": row[0],
                    "type": row[1],
                    "account": row[2],
                    "category": row[3],
                    "amount": row[4],
                    "to_account": row[5],
                    "comment": row[6],
                    "full_date": row[7] if len(row) > 7 else "",
                    "hours": row[8] if len(row) > 8 else ""
                })

        return transactions[-limit:][::-1]  # Последние N, в обратном порядке

    def get_income_by_days(self) -> Dict[str, Any]:
        """Получить доходы по дням с детализацией"""
        sheet = self.spreadsheet.worksheet(config.SHEET_TRANSACTIONS)
        data = sheet.get_all_values()

        # Группируем доходы по дням
        income_by_day = {}

        for row in data[3:]:  # Пропускаем настройки и заголовки
            if row[0] and row[0].strip() and len(row) > 1:
                if row[1] == "Доход":  # Только доходы
                    day = row[0]
                    amount = safe_float(row[4])
                    category = row[3] if len(row) > 3 else ""
                    comment = row[6] if len(row) > 6 else ""
                    hours = safe_float(row[8]) if len(row) > 8 else 0

                    if day not in income_by_day:
                        income_by_day[day] = {
                            "total": 0,
                            "tips": 0,
                            "hours": 0,
                            "other": 0,
                            "entries": []
                        }

                    income_by_day[day]["total"] += amount

                    # Разделяем на чаевые и другое
                    if category == "Зарплата/Чаевые":
                        income_by_day[day]["tips"] += amount
                        income_by_day[day]["hours"] += hours
                    else:
                        income_by_day[day]["other"] += amount

                    income_by_day[day]["entries"].append({
                        "amount": amount,
                        "category": category,
                        "comment": comment,
                        "hours": hours
                    })

        # Сортируем по дням
        sorted_days = sorted(income_by_day.keys(), key=lambda x: int(x) if x.isdigit() else 0)

        return {
            "by_day": income_by_day,
            "sorted_days": sorted_days,
            "total_income": sum(d["total"] for d in income_by_day.values()),
            "total_tips": sum(d["tips"] for d in income_by_day.values()),
            "total_hours": sum(d["hours"] for d in income_by_day.values())
        }


# Создаем глобальный экземпляр
sheets_service = None

def get_sheets_service() -> GoogleSheetsService:
    """Получить экземпляр сервиса (singleton)"""
    global sheets_service
    if sheets_service is None:
        sheets_service = GoogleSheetsService()
    return sheets_service
