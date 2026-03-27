import { useCallback, useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { getMonthlySummary, createTransaction, getReferences } from '../api/client';
import { DashboardSkeleton } from '../components/Skeleton';
import { useToast } from '../components/Toast';
import { ChevronLeft, ChevronRight, ChevronDown, ChevronUp, TrendingUp, TrendingDown, AlertTriangle, Send, Plus } from 'lucide-react';
import type { MonthlySummary, References } from '../types';

const MONTH_NAMES = ['', 'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
  'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'];

function formatMoney(value: number | null | undefined, currency = 'BYN'): string {
  return `${(value ?? 0).toFixed(2)} ${currency}`;
}

function getGreeting(): string {
  const h = new Date().getHours();
  if (h < 6) return 'Доброй ночи';
  if (h < 12) return 'Доброе утро';
  if (h < 18) return 'Добрый день';
  return 'Добрый вечер';
}

function getDaysLeft(): number {
  const now = new Date();
  const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate();
  return lastDay - now.getDate();
}

export default function DashboardPage() {
  const now = new Date();
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [year, setYear] = useState(now.getFullYear());
  const [summary, setSummary] = useState<MonthlySummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCategories, setShowCategories] = useState(false);
  const [quickInput, setQuickInput] = useState('');
  const [quickLoading, setQuickLoading] = useState(false);
  const [refs, setRefs] = useState<References | null>(null);
  const navigate = useNavigate();
  const location = useLocation();
  const { showToast } = useToast();

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
    setLoading(true); setError(''); setSummary(null);
    getMonthlySummary(month, year)
      .then(setSummary)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [month, year]);

  useEffect(load, [location.key, load]);
  useEffect(() => { getReferences().then(setRefs).catch(() => {}); }, []);

  // R2: Quick input parser "500 продукты" or "100"
  const handleQuickSubmit = async () => {
    const text = quickInput.trim();
    if (!text || quickLoading) return;

    const parts = text.split(/\s+/);
    const amount = parseFloat(parts[0]);
    if (!amount || amount <= 0) {
      showToast('Введите сумму, например: 50 продукты', 'error');
      return;
    }

    // Try to match category
    let category = '';
    if (parts.length > 1) {
      const catText = parts.slice(1).join(' ').toLowerCase();
      const allCats = refs?.categories || [];
      const match = allCats.find((c) => c.toLowerCase().startsWith(catText));
      if (match) {
        category = match;
      } else {
        showToast(`Категория "${parts.slice(1).join(' ')}" не найдена`, 'error');
        return;
      }
    }

    setQuickLoading(true);
    try {
      await createTransaction({
        type: 'Расход',
        account: refs?.accounts?.[0] || 'Наличные',
        amount,
        category: category || (refs?.categories?.[0] || 'Продукты'),
        date: (() => { const d = new Date(); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`; })(),
      });
      window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('success');
      showToast(`-${amount} BYN${category ? ` · ${category}` : ''}`, 'success');
      setQuickInput('');
      load();
    } catch {
      window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('error');
      showToast('Ошибка сохранения', 'error');
    } finally {
      setQuickLoading(false);
    }
  };

  if (loading) return <DashboardSkeleton />;
  if (error) return (
    <div className="page">
      <div className="error-box" role="alert">
        <AlertTriangle size={48} color="var(--danger)" />
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
        <div className="empty-icon">
          <TrendingUp size={48} />
        </div>
        <div className="empty-text">Нет данных за этот период</div>
        <div className="empty-hint">Добавьте первую транзакцию</div>
        <button className="empty-action" onClick={() => navigate('/add')}>
          <Plus size={16} /> Добавить
        </button>
      </div>
    </div>
  );

  const expenseCategories = summary.categories
    .filter((c) => c.type === 'Расход' && c.spent > 0)
    .sort((a, b) => b.spent - a.spent);

  const daysLeft = getDaysLeft();
  const netBalance = (summary.total_income || 0) - (summary.total_expense || 0);

  return (
    <div className="page">
      {/* R8: Hero block with greeting */}
      <div className="hero-balance">
        <div className="hero-greeting">{getGreeting()}, Артур</div>
        <div className="hero-amount" style={{ color: netBalance >= 0 ? 'var(--success)' : 'var(--danger)' }}>
          {netBalance >= 0 ? '+' : ''}{formatMoney(netBalance)}
        </div>
        <div className="hero-label">
          Баланс за {MONTH_NAMES[month].toLowerCase()}
          {isCurrentMonth && daysLeft > 0 && ` · ${daysLeft} дн. до конца`}
        </div>

        {/* R6: Account chips */}
        <div className="hero-accounts" role="list" aria-label="Счета">
          {summary.accounts.map((acc) => (
            <div
              className="hero-account-chip"
              key={acc.name}
              role="button"
              tabIndex={0}
              style={{ cursor: 'pointer' }}
              onClick={() => navigate(`/history?account=${encodeURIComponent(acc.name)}`)}
              onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); navigate(`/history?account=${encodeURIComponent(acc.name)}`); }}}
            >
              <span>{acc.emoji || '💳'}</span>
              <span className="chip-name">{acc.name}</span>
              <span className="amount">{formatMoney(acc.current, acc.currency)}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Month selector */}
      <div className="month-selector">
        <button className="month-btn" onClick={prevMonth} aria-label="Предыдущий месяц">
          <ChevronLeft size={18} />
        </button>
        <span className="month-selector-label">
          {MONTH_NAMES[month]} {year}
        </span>
        <button
          className="month-btn"
          onClick={nextMonth}
          disabled={isCurrentMonth}
          aria-label="Следующий месяц"
        >
          <ChevronRight size={18} />
        </button>
      </div>

      {/* R2: Quick input */}
      {isCurrentMonth && (
        <div className="quick-input-wrap">
          <input
            className="quick-input"
            type="text"
            inputMode="text"
            placeholder="50 продукты..."
            value={quickInput}
            onChange={(e) => setQuickInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleQuickSubmit()}
            aria-label="Быстрый ввод расхода"
          />
          <button
            className="quick-input-btn"
            onClick={handleQuickSubmit}
            disabled={quickLoading || !quickInput.trim()}
            aria-label="Добавить расход"
          >
            <Send size={20} />
          </button>
        </div>
      )}

      {/* Income / Expense summary */}
      <div className="grid-2">
        <div className="card" style={{ cursor: 'pointer' }} onClick={() => navigate('/income')} onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); navigate('/income'); }}} role="button" tabIndex={0} aria-label="Посмотреть доходы">
          <div className="card-title">
            <TrendingUp size={12} style={{ verticalAlign: 'middle', marginRight: 4 }} />
            Доходы
          </div>
          <div className="stat-value amount income">{formatMoney(summary.total_income)}</div>
        </div>
        <div className="card" style={{ cursor: 'pointer' }} onClick={() => navigate(`/expenses?month=${month}&year=${year}`)} onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); navigate(`/expenses?month=${month}&year=${year}`); }}} role="button" tabIndex={0} aria-label="Посмотреть расходы">
          <div className="card-title">
            <TrendingDown size={12} style={{ verticalAlign: 'middle', marginRight: 4 }} />
            Расходы
          </div>
          <div className="stat-value amount expense">{formatMoney(summary.total_expense)}</div>
        </div>
      </div>

      {/* Budget warnings */}
      {summary.over_budget.length > 0 && summary.over_budget.map((cat) => (
        <div className="warning-card danger" key={cat.name} role="alert">
          <span className="warning-icon">🚨</span>
          <div>
            <strong>{cat.emoji} {cat.name}</strong>: {cat.spent.toFixed(2)} / {cat.budget.toFixed(0)} BYN
          </div>
        </div>
      ))}
      {summary.near_limit.length > 0 && summary.near_limit.map((cat) => (
        <div className="warning-card warning" key={cat.name} role="alert">
          <span className="warning-icon">⚠️</span>
          <div>
            <strong>{cat.emoji} {cat.name}</strong>: {cat.spent.toFixed(2)} / {cat.budget.toFixed(0)} BYN
          </div>
        </div>
      ))}

      {/* R6: Collapsible expense categories */}
      {expenseCategories.length > 0 && (
        <div className="card">
          <button
            className="section-toggle"
            onClick={() => setShowCategories(!showCategories)}
            aria-expanded={showCategories}
            aria-controls="categories-list"
          >
            <span>Расходы по категориям ({expenseCategories.length})</span>
            {showCategories ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>

          {/* Always show top 3, expand for rest */}
          <div id="categories-list">
            {(showCategories ? expenseCategories : expenseCategories.slice(0, 3)).map((cat) => {
              const pct = cat.budget > 0 ? Math.min(cat.progress * 100, 100) : 0;
              const status = cat.progress >= 1 ? 'over' : cat.progress >= 0.8 ? 'warn' : 'ok';
              return (
                <div key={cat.name} style={{ marginBottom: 10 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                    <span>{cat.emoji} {cat.name}</span>
                    <span className="amount expense">
                      {cat.spent.toFixed(2)}
                      {cat.budget > 0 && <span className="stat-label"> / {cat.budget.toFixed(0)}</span>}
                    </span>
                  </div>
                  {cat.budget > 0 && (
                    <div className="progress-bar" role="progressbar" aria-valuenow={Math.round(pct)} aria-valuemin={0} aria-valuemax={100} aria-label={`${cat.name}: ${cat.spent.toFixed(0)} из ${cat.budget.toFixed(0)} BYN`}>
                      <div className={`progress-fill ${status}`} style={{ width: `${pct}%` }} />
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {!showCategories && expenseCategories.length > 3 && (
            <button
              style={{
                background: 'none', border: 'none', color: 'var(--accent)',
                fontSize: 13, cursor: 'pointer', padding: '4px 0', width: '100%', textAlign: 'center',
              }}
              onClick={() => setShowCategories(true)}
            >
              Ещё {expenseCategories.length - 3} категорий
            </button>
          )}
        </div>
      )}

    </div>
  );
}
