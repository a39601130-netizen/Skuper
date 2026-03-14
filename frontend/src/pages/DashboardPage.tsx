import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getMonthlySummary, getIncomeStats } from '../api/client';
import type { MonthlySummary } from '../types';
import ExpensePieChart from '../components/charts/ExpensePieChart';
import SpendingTrendChart from '../components/charts/SpendingTrendChart';
import InsightsCard from '../components/InsightsCard';
import RecurringTransactionsList from '../components/RecurringTransactionsList';

function formatMoney(value: number, currency = 'BYN'): string {
  return `${value.toFixed(2)} ${currency}`;
}

interface IncomeDay {
  day: number;
  date: string;
  total: number;
  salary: number;
  tips: number;
  other: number;
  hours: number;
  transactions: { id: number; amount: number; currency: string; category: string; comment: string; hours: number | null }[];
}

interface IncomeStats {
  month: number;
  year: number;
  days: IncomeDay[];
  total_income: number;
  total_hours: number;
  base_hourly_rate: number;
}

export default function DashboardPage() {
  const [summary, setSummary] = useState<MonthlySummary | null>(null);
  const [incomeStats, setIncomeStats] = useState<IncomeStats | null>(null);
  const [showIncome, setShowIncome] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    getMonthlySummary()
      .then(setSummary)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="page"><div className="loading">Загрузка...</div></div>;
  if (error) return (
    <div className="page">
      <div className="error-box">
        <div className="error-icon">⚠️</div>
        <div className="error-text">{error}</div>
        <button className="btn btn-primary" onClick={() => window.location.reload()}>
          Повторить
        </button>
      </div>
    </div>
  );
  if (!summary) return (
    <div className="page">
      <div className="empty">
        <div className="empty-icon">📊</div>
        <div>Нет данных</div>
      </div>
    </div>
  );

  const expenseCategories = summary.categories
    .filter((c) => c.type === 'Расход' && c.spent > 0)
    .sort((a, b) => b.spent - a.spent);

  return (
    <div className="page">
      <h1 className="page-title">Финансы</h1>

      {/* Сводка */}
      <div className="grid-2">
        <div className="card" onClick={() => {
          if (!incomeStats) {
            getIncomeStats().then((d) => setIncomeStats(d as unknown as IncomeStats)).catch(() => {});
          }
          setShowIncome(!showIncome);
        }} style={{ cursor: 'pointer' }}>
          <div className="card-title">Доходы {showIncome ? '▲' : '▼'}</div>
          <div className="stat-value amount income">{formatMoney(summary.total_income)}</div>
        </div>
        <div className="card">
          <div className="card-title">Расходы</div>
          <div className="stat-value amount expense">{formatMoney(summary.total_expense)}</div>
        </div>
      </div>

      {/* Доходы по дням */}
      {showIncome && incomeStats && (
        <div className="card">
          <div className="card-title">Доходы по дням</div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12, fontSize: 13 }}>
            <span>Всего часов: <strong>{incomeStats.total_hours.toFixed(1)}</strong></span>
            <span>Ставка: <strong>{incomeStats.base_hourly_rate} BYN/ч</strong></span>
          </div>
          {incomeStats.days.length === 0 && (
            <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Нет доходов за этот месяц</div>
          )}
          {incomeStats.days.map((day) => (
            <div key={day.date} style={{
              padding: '10px 0', borderBottom: '1px solid var(--border)',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                <span style={{ fontWeight: 600 }}>{day.date}</span>
                <span className="amount income" style={{ fontWeight: 600 }}>
                  {formatMoney(day.total)}
                </span>
              </div>
              <div style={{ display: 'flex', gap: 12, fontSize: 12, color: 'var(--text-secondary)' }}>
                {day.salary > 0 && <span>Зарплата: {day.salary.toFixed(0)}</span>}
                {day.tips > 0 && <span>Чаевые: {day.tips.toFixed(0)}</span>}
                {day.other > 0 && <span>Другое: {day.other.toFixed(0)}</span>}
                {day.hours > 0 && <span>{day.hours}ч</span>}
              </div>
              {day.transactions.length > 1 && (
                <div style={{ marginTop: 4 }}>
                  {day.transactions.map((tx) => (
                    <div key={tx.id} style={{ fontSize: 11, color: 'var(--text-secondary)', paddingLeft: 8 }}>
                      {tx.category || 'Доход'}: {tx.amount} {tx.currency}
                      {tx.comment && ` — ${tx.comment}`}
                      {tx.hours && ` (${tx.hours}ч)`}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      <div className="card">
        <div className="card-title">Баланс</div>
        <div className="stat-value">{formatMoney(summary.balance)}</div>
        <div className="stat-label">На счетах: {formatMoney(summary.total_on_accounts)}</div>
      </div>

      {/* Счета (группировка по валюте) */}
      <div className="card">
        <div className="card-title">Счета</div>
        {(() => {
          const byCurrency: Record<string, typeof summary.accounts> = {};
          for (const acc of summary.accounts) {
            if (!byCurrency[acc.currency]) byCurrency[acc.currency] = [];
            byCurrency[acc.currency].push(acc);
          }
          return Object.entries(byCurrency).map(([currency, accs]) => (
            <div key={currency}>
              {Object.keys(byCurrency).length > 1 && (
                <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 8, marginBottom: 4 }}>
                  {currency} — итого: {formatMoney(accs.reduce((s, a) => s + a.current, 0), currency)}
                </div>
              )}
              {accs.map((acc) => (
                <div className="list-item" key={acc.name}>
                  <span className="list-item-icon">{acc.emoji || '💳'}</span>
                  <div className="list-item-content">
                    <div className="list-item-title">{acc.name}</div>
                  </div>
                  <div className="list-item-right">
                    <span className="amount">{formatMoney(acc.current, acc.currency)}</span>
                  </div>
                </div>
              ))}
            </div>
          ));
        })()}
      </div>

      {/* Категории расходов с бюджетами */}
      {expenseCategories.length > 0 && (
        <div className="card">
          <div className="card-title">Расходы по категориям</div>
          {expenseCategories.map((cat) => {
            const pct = cat.budget > 0 ? Math.min(cat.progress * 100, 100) : 0;
            const status = cat.progress >= 1 ? 'over' : cat.progress >= 0.8 ? 'warn' : 'ok';
            return (
              <div key={cat.name} style={{ marginBottom: 12 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <span>{cat.emoji} {cat.name}</span>
                  <span className="amount expense">
                    {cat.spent.toFixed(0)}
                    {cat.budget > 0 && <span className="stat-label"> / {cat.budget.toFixed(0)}</span>}
                  </span>
                </div>
                {cat.budget > 0 && (
                  <div className="progress-bar">
                    <div className={`progress-fill ${status}`} style={{ width: `${pct}%` }} />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Графики */}
      <ExpensePieChart categories={summary.categories} />
      <SpendingTrendChart />

      {/* AI инсайты */}
      <InsightsCard />

      {/* Повторяющиеся транзакции */}
      <RecurringTransactionsList />

      {/* Быстрое добавление */}
      <button className="btn btn-primary btn-full" onClick={() => navigate('/add')}>
        ➕ Добавить транзакцию
      </button>
    </div>
  );
}
