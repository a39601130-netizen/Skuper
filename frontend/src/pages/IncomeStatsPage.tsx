import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getIncomeStats } from '../api/client';
import type { IncomeStats } from '../types';

const MONTH_NAMES = ['', 'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
  'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'];

export default function IncomeStatsPage() {
  const navigate = useNavigate();
  const now = new Date();
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [year, setYear] = useState(now.getFullYear());
  const [stats, setStats] = useState<IncomeStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const isCurrentMonth = month === now.getMonth() + 1 && year === now.getFullYear();

  const prevMonth = () => {
    if (month === 1) { setMonth(12); setYear(y => y - 1); }
    else setMonth(m => m - 1);
  };
  const nextMonth = () => {
    if (isCurrentMonth) return;
    if (month === 12) { setMonth(1); setYear(y => y + 1); }
    else setMonth(m => m + 1);
  };

  const load = useCallback(() => {
    setLoading(true); setError('');
    getIncomeStats(month, year)
      .then(setStats)
      .catch((e) => setError(e.message || 'Ошибка загрузки'))
      .finally(() => setLoading(false));
  }, [month, year]);

  useEffect(load, [load]);

  if (loading) return <div className="page"><div className="loading">Загрузка...</div></div>;
  if (error) return (
    <div className="page">
      <div className="error-box">
        <div className="error-icon">⚠️</div>
        <div className="error-text">{error}</div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-ghost" onClick={() => navigate(-1)}>← Назад</button>
          <button className="btn btn-primary" onClick={load}>Повторить</button>
        </div>
      </div>
    </div>
  );
  if (!stats) return <div className="page"><div className="empty"><div className="empty-icon">📊</div>Нет данных</div></div>;

  const avgPerHour = stats.total_hours > 0 ? (stats.total_income / stats.total_hours).toFixed(2) : '—';

  return (
    <div className="page">
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
        <button className="btn btn-ghost" onClick={() => navigate(-1)} style={{ padding: '4px 12px', fontSize: 14 }}>← Назад</button>
        <h1 className="page-title" style={{ margin: 0 }}>Доходы</h1>
      </div>

      {/* Month selector */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        gap: 12, marginBottom: 12,
      }}>
        <button className="btn btn-ghost" onClick={prevMonth} style={{ padding: '4px 12px' }}>
          ←
        </button>
        <span style={{ fontWeight: 600, fontSize: 15, minWidth: 130, textAlign: 'center' }}>
          {MONTH_NAMES[month]} {year}
        </span>
        <button
          className="btn btn-ghost"
          onClick={nextMonth}
          disabled={isCurrentMonth}
          style={{ padding: '4px 12px', opacity: isCurrentMonth ? 0.3 : 1 }}
        >
          →
        </button>
      </div>

      {/* Summary */}
      <div className="grid-2">
        <div className="card">
          <div className="card-title">Всего</div>
          <div className="stat-value amount income">{stats.total_income.toFixed(2)} BYN</div>
        </div>
        <div className="card">
          <div className="card-title">Часов</div>
          <div className="stat-value">{stats.total_hours.toFixed(1)}</div>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-title">Ставка</div>
          <div className="stat-value">{stats.base_hourly_rate} BYN/ч</div>
        </div>
        <div className="card">
          <div className="card-title">Факт/ч</div>
          <div className="stat-value">{avgPerHour} BYN</div>
        </div>
      </div>

      {/* Days */}
      {stats.days.length === 0 ? (
        <div className="empty">Нет доходов за этот месяц</div>
      ) : (
        <div className="card" style={{ padding: 0 }}>
          {stats.days.map((day) => (
            <div className="list-item" key={day.day} style={{ flexDirection: 'column', alignItems: 'stretch' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                <span style={{ fontWeight: 600 }}>{day.date}</span>
                <span className="amount income">+{day.total.toFixed(2)} BYN</span>
              </div>
              <div style={{ display: 'flex', gap: 12, fontSize: 13, color: 'var(--text-secondary)' }}>
                {day.salary > 0 && <span>💰 {day.salary.toFixed(0)}</span>}
                {day.tips > 0 && <span>💵 {day.tips.toFixed(0)}</span>}
                {day.other > 0 && <span>📦 {day.other.toFixed(0)}</span>}
                {day.hours > 0 && <span>🕐 {day.hours}ч</span>}
              </div>
              {(day.transactions.length > 1 || day.transactions.some(t => t.comment)) && (
                <div style={{ marginTop: 4, fontSize: 12, color: 'var(--text-muted)' }}>
                  {day.transactions.map((t) => (
                    <div key={t.id}>
                      {day.transactions.length > 1 && <>{t.category}: {t.amount} {t.currency}</>}
                      {t.comment ? (day.transactions.length > 1 ? ` — ${t.comment}` : `💬 ${t.comment}`) : ''}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
