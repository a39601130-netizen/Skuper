"""
AI Советник на базе DeepSeek
"""
import httpx
from typing import Dict, Any, Optional
import config

class AIAdvisor:
    """AI советник для финансовых рекомендаций"""
    
    def __init__(self):
        self.api_key = config.DEEPSEEK_API_KEY
        self.api_url = config.DEEPSEEK_API_URL
        self.user_name = config.USER_NAME
        self.hd_context = config.HUMAN_DESIGN_CONTEXT
    
    async def get_advice(
        self, 
        budget_data: Dict[str, Any],
        user_question: Optional[str] = None
    ) -> str:
        """
        Получить совет от AI на основе данных бюджета
        
        Args:
            budget_data: Данные из get_monthly_summary()
            user_question: Опциональный вопрос пользователя
        
        Returns:
            str: Совет от AI
        """
        
        # Формируем контекст с данными бюджета
        budget_context = self._format_budget_context(budget_data)
        
        # Системный промпт
        system_prompt = f"""Ты - персональный финансовый AI-советник для {self.user_name}.

{self.hd_context}

## ПРАВИЛА ОБЩЕНИЯ
- Без осуждения, с фокусом на решения
- При вопросах о больших покупках: проверяй "это ХОЧУ или ДОЛЖЕН?"
- Учитывай эмоциональный авторитет: не торопи с решениями
- Напоминай о Human Design профиле при важных выборах

## КОНТЕКСТ МОТИВАЦИИ
- Ценность {self.user_name} НЕ измеряется часами работы
- Его талант: системное видение, объяснение сложного просто
- Работа официантом — временный этап, не идентичность
- Каждый сохранённый рубль = шаг к свободе и признанию

## ФОРМАТ ОТВЕТА
📊 [Краткий анализ ситуации]
💡 [1-2 практических действия]
🎯 [Связь с целью/мотивация]

При необходимости добавь:
⚠️ [Предупреждение для эмоционального авторитета]
✨ [Признание достижения]

## СТИЛЬ
- Краткие сообщения (до 500 символов)
- Конкретные цифры и действия
- Используй эмодзи для структуры
- Обращайся на "ты"

ВАЖНО: Отвечай на русском языке!"""

        # Пользовательский запрос
        if user_question:
            user_prompt = f"""Текущее состояние бюджета:
{budget_context}

Вопрос пользователя: {user_question}

Дай персонализированный совет."""
        else:
            user_prompt = f"""Текущее состояние бюджета:
{budget_context}

Проанализируй ситуацию и дай краткий совет дня. 
Если есть проблемы - укажи их. Если всё хорошо - похвали."""

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.api_url,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.api_key}"
                    },
                    json={
                        "model": "deepseek-chat",
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "max_tokens": 500,
                        "temperature": 0.7
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    return f"❌ Ошибка API: {response.status_code}"
                    
        except httpx.TimeoutException:
            return "⏳ AI советник временно недоступен. Попробуй позже."
        except Exception as e:
            return f"❌ Ошибка: {str(e)}"
    
    def _format_budget_context(self, data: Dict[str, Any]) -> str:
        """Форматировать данные бюджета для AI"""
        
        lines = [
            f"📊 Доходы за месяц: {data['total_income']} BYN",
            f"💸 Расходы за месяц: {data['total_expense']} BYN", 
            f"📈 Баланс: {data['balance']} BYN",
            ""
        ]
        
        # Счета
        lines.append("💳 Счета:")
        for acc in data.get("accounts", []):
            lines.append(f"  • {acc['name']}: {acc['current']} {acc['currency']}")
        
        # Категории расходов с бюджетами
        lines.append("\n📁 Расходы по категориям:")
        for cat in data.get("categories", []):
            if cat["type"] == "Расход" and cat["budget"] > 0:
                progress_pct = int(cat["progress"] * 100)
                status = "⚠️" if progress_pct >= 80 else "✅"
                lines.append(
                    f"  {status} {cat['name']}: {cat['spent']}/{cat['budget']} BYN ({progress_pct}%)"
                )
        
        # Предупреждения
        if data.get("over_budget"):
            lines.append("\n🚨 ПРЕВЫШЕНИЕ БЮДЖЕТА:")
            for cat in data["over_budget"]:
                over = cat["spent"] - cat["budget"]
                lines.append(f"  • {cat['name']}: +{over} BYN сверх лимита!")
        
        if data.get("near_limit"):
            lines.append("\n⚠️ Близко к лимиту:")
            for cat in data["near_limit"]:
                remaining = cat["remaining"]
                lines.append(f"  • {cat['name']}: осталось {remaining} BYN")
        
        return "\n".join(lines)


# Создаем глобальный экземпляр
_advisor = None

def get_advisor() -> AIAdvisor:
    """Получить экземпляр советника (singleton)"""
    global _advisor
    if _advisor is None:
        _advisor = AIAdvisor()
    return _advisor
