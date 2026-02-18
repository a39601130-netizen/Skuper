"""
DeepSeek AI Советник
Интеграция с DeepSeek API для анализа и рекомендаций
"""
import logging
import httpx
import re
from typing import Optional
import config

# Предкомпилированные регулярные выражения для производительности
_HEADER_PATTERNS = [
    (re.compile(r'^### (.+)$', re.MULTILINE), r'**\1**'),
    (re.compile(r'^## (.+)$', re.MULTILINE), r'**\1**'),
    (re.compile(r'^# (.+)$', re.MULTILINE), r'**\1**'),
]

logger = logging.getLogger(__name__)


class AIAdvisor:
    """Класс для работы с DeepSeek AI"""
    
    def __init__(self):
        self.api_key = config.DEEPSEEK_API_KEY
        self.api_url = config.DEEPSEEK_API_URL
        self.model = config.DEEPSEEK_MODEL
        self.hd_context = config.HUMAN_DESIGN_CONTEXT
    
    async def ask(
        self,
        question: str,
        context: Optional[str] = None,
        mode: str = "default",
        use_reasoner: bool = False
    ) -> str:
        """
        Отправить вопрос к DeepSeek
        
        Args:
            question: Вопрос пользователя
            context: Дополнительный контекст (данные тренировок, финансов)
            mode: Режим ответа (default, brief, detailed)
        
        Returns:
            Ответ от AI
        """
        if not self.api_key:
            return "❌ API ключ DeepSeek не настроен"
        
        # Формируем системный промпт
        system_prompt = self._build_system_prompt(mode)
        
        # Формируем сообщение с контекстом
        user_message = question
        if context:
            user_message = f"{context}\n\n---\nВопрос: {question}"
        
        model = "deepseek-reasoner" if use_reasoner else self.model
        temperature = 0.4 if use_reasoner or mode in ("default", "detailed") else 0.7
        max_tokens = 1500 if mode == "detailed" else 1200

        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                response = await client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_message}
                        ],
                        "temperature": temperature,
                        "max_tokens": max_tokens
                    }
                )
                
                response.raise_for_status()
                data = response.json()

                answer = data["choices"][0]["message"]["content"]

                # Постобработка: заменяем ### на жирный текст (Telegram не поддерживает заголовки)
                for pattern, replacement in _HEADER_PATTERNS:
                    answer = pattern.sub(replacement, answer)

                return answer
                
        except httpx.TimeoutException:
            logger.error("DeepSeek API timeout")
            return "⏱️ Превышено время ожидания. Попробуй позже."
        except httpx.HTTPStatusError as e:
            logger.error(f"DeepSeek API error: {e}")
            return f"❌ Ошибка API: {e.response.status_code}"
        except Exception as e:
            logger.error(f"DeepSeek unexpected error: {e}")
            return "❌ Произошла ошибка при обращении к AI"
    
    def _build_system_prompt(self, mode: str) -> str:
        """Построить системный промпт в зависимости от режима"""
        
        base_prompt = f"""Ты - персональный AI-помощник для Артура.

{self.hd_context}

ТВОЯ РОЛЬ:
- Анализировать данные тренировок и финансов
- Давать персонализированные рекомендации
- Учитывать Human Design при советах
- Быть поддерживающим, но честным
- Говорить на русском языке
"""
        
        if mode == "brief":
            base_prompt += """
ФОРМАТ ОТВЕТА:
- Кратко и по делу (2-3 предложения)
- Используй emoji для структуры
- Без лишних объяснений
- ВАЖНО: Используй только **жирный текст** для заголовков, НЕ используй # или ## или ###
- Поддерживаемый формат: **жирный**, _курсив_, строки с emoji
"""
        elif mode == "detailed":
            base_prompt += """
ФОРМАТ ОТВЕТА:
- Подробный анализ с объяснениями
- Структурируй информацию
- Приводи конкретные цифры и рекомендации
- Используй emoji для наглядности
- ВАЖНО: Используй только **жирный текст** для заголовков, НЕ используй # или ## или ###
- Поддерживаемый формат: **жирный**, _курсив_, строки с emoji
"""
        else:  # default
            base_prompt += """
ФОРМАТ ОТВЕТА:
- Сбалансированный по длине
- Конкретные рекомендации
- Используй emoji умеренно
- ВАЖНО: Используй только **жирный текст** для заголовков, НЕ используй # или ## или ###
- Поддерживаемый формат: **жирный**, _курсив_, строки с emoji
"""
        
        return base_prompt
    
    async def analyze_workout(
        self,
        workout_data: dict,
        history: list,
        trigger: str = "manual"
    ) -> str:
        """
        Анализ тренировки
        
        Args:
            workout_data: Данные текущей тренировки
            history: История последних тренировок
            trigger: Что вызвало анализ (manual, low_energy, high_rpe, etc.)
        
        Returns:
            Анализ и рекомендации
        """
        context = self._format_workout_context(workout_data, history, trigger)
        
        prompts = {
            "manual": "Проанализируй мою тренировку и дай рекомендации.",
            "low_energy": "Моя энергия сегодня низкая. Что посоветуешь?",
            "high_rpe": "Последние тренировки были очень тяжёлыми (RPE 9+). Это проблема?",
            "back_pain": "Боль в спине выше обычного. Как адаптировать тренировку?",
            "phase_transition": "Я перехожу в новую фазу программы. Что меняется?",
            "weekly": "Подведи итоги недели тренировок.",
        }
        
        question = prompts.get(trigger, prompts["manual"])
        mode = "brief" if trigger in ["low_energy", "high_rpe", "back_pain"] else "default"
        
        return await self.ask(question, context, mode)
    
    async def analyze_finance(
        self,
        finance_data: dict,
        period: str = "month"
    ) -> str:
        """
        Анализ финансов
        
        Args:
            finance_data: Данные по финансам
            period: Период анализа (week, month, year)
        """
        context = self._format_finance_context(finance_data, period)
        question = f"Проанализируй мои финансы за {period} и дай рекомендации."
        
        return await self.ask(question, context, "default")
    
    def _format_workout_context(
        self,
        workout_data: dict,
        history: list,
        trigger: str
    ) -> str:
        """Форматировать контекст тренировки для AI"""
        
        context_parts = ["📊 ДАННЫЕ ТРЕНИРОВКИ:"]
        
        if workout_data:
            context_parts.append(f"""
Текущая тренировка:
- День: {workout_data.get('day_type', 'N/A')}
- Неделя: {workout_data.get('week_num', 'N/A')}
- Фаза: {workout_data.get('phase', 'N/A')}
- Энергия до: {workout_data.get('energy_before', 'N/A')}/10
- Сон: {workout_data.get('sleep_hours', 'N/A')} часов
- Боль в спине: {workout_data.get('back_pain', 'N/A')}/10
- Эмоциональная волна: {workout_data.get('emotional_wave', 'N/A')}
""")
        
        if history:
            context_parts.append("\nИстория последних тренировок:")
            for i, h in enumerate(history[-5:], 1):
                context_parts.append(
                    f"{i}. {h.get('date', 'N/A')} - День {h.get('day_type', 'N/A')}, "
                    f"энергия: {h.get('energy_before', '?')}→{h.get('energy_after', '?')}"
                )
        
        if trigger != "manual":
            context_parts.append(f"\n⚠️ Триггер анализа: {trigger}")
        
        return "\n".join(context_parts)
    
    def _format_finance_context(self, finance_data: dict, period: str) -> str:
        """Форматировать контекст финансов для AI"""
        
        return f"""📊 ФИНАНСОВЫЕ ДАННЫЕ ({period}):

Доходы: {finance_data.get('income', 0)} BYN
Расходы: {finance_data.get('expenses', 0)} BYN
Баланс: {finance_data.get('balance', 0)} BYN

Топ категории расходов:
{finance_data.get('top_expenses', 'Нет данных')}

Рабочие часы: {finance_data.get('work_hours', 0)} ч
"""



    async def get_advice(
        self,
        budget_data: dict,
        user_question: str = None
    ) -> str:
        """Получить совет от AI на основе данных бюджета"""
        context = self._format_budget_context(budget_data)
        question = user_question or 'Проанализируй финансовую ситуацию за месяц. Укажи тренды, превышения и дай конкретные рекомендации.'
        # Для глубокого анализа используем reasoner, для вопросов — обычную модель
        use_reasoner = user_question is None
        return await self.ask(question, context, 'default', use_reasoner=use_reasoner)

    def _format_budget_context(self, data: dict) -> str:
        """Форматировать данные бюджета для AI"""
        from datetime import datetime
        today = datetime.now()
        days_in_month = 30
        days_passed = today.day
        month_progress_pct = int(days_passed / days_in_month * 100)

        total_income = data.get('total_income', 0)
        total_expense = data.get('total_expense', 0)

        lines = [
            f"📅 Текущая дата: {today.strftime('%d.%m.%Y')} (прошло {days_passed} дней из ~{days_in_month}, {month_progress_pct}% месяца)",
            f"📊 Доходы за месяц: {total_income} BYN",
            f"💸 Расходы за месяц: {total_expense} BYN",
            f"📈 Баланс: {data.get('balance', 0)} BYN",
        ]

        # Тренд расходов: сравниваем с ожидаемым на текущую дату
        if total_expense > 0 and days_passed > 0:
            daily_rate = total_expense / days_passed
            projected_month = daily_rate * days_in_month
            lines.append(f"📉 Темп расходов: {daily_rate:.1f} BYN/день → прогноз на месяц: {projected_month:.0f} BYN")

        # Заработок в час
        total_hours = data.get('total_hours', 0)
        if total_hours and total_hours > 0:
            total_tips = data.get('total_tips', total_income)
            hourly = total_tips / total_hours
            lines.append(f"⏰ Отработано: {total_hours:.1f} ч → {hourly:.2f} BYN/ч")

        lines.append('')
        lines.append('💳 Счета:')
        for acc in data.get('accounts', []):
            lines.append(f"  • {acc['name']}: {acc['current']} {acc['currency']}")

        lines.append('')
        lines.append('📁 Расходы по категориям:')
        for cat in data.get('categories', []):
            if cat.get('type') == 'Расход' and cat.get('budget', 0) > 0:
                progress_pct = int(cat.get('progress', 0) * 100)
                # Тренд: если прогресс расходов сильно опережает прогресс месяца
                if progress_pct > month_progress_pct + 20:
                    trend = "📈 опережает"
                elif progress_pct < month_progress_pct - 20:
                    trend = "📉 в норме"
                else:
                    trend = ""
                status = '⚠️' if progress_pct >= 80 else '✅'
                trend_str = f" {trend}" if trend else ""
                lines.append(f"  {status} {cat['name']}: {cat['spent']}/{cat['budget']} BYN ({progress_pct}%){trend_str}")

        if data.get('over_budget'):
            lines.append('')
            lines.append('🚨 ПРЕВЫШЕНИЕ БЮДЖЕТА:')
            for cat in data['over_budget']:
                over = cat['spent'] - cat['budget']
                lines.append(f"  • {cat['name']}: +{over} BYN сверх лимита!")

        if data.get('near_limit'):
            lines.append('')
            lines.append('⚠️ Близко к лимиту:')
            for cat in data['near_limit']:
                lines.append(f"  • {cat['name']}: осталось {cat['remaining']} BYN")

        return '\n'.join(lines)

# Синглтон для использования
_advisor_instance = None

def get_advisor() -> AIAdvisor:
    """Получить экземпляр AI советника"""
    global _advisor_instance
    if _advisor_instance is None:
        _advisor_instance = AIAdvisor()
    return _advisor_instance
