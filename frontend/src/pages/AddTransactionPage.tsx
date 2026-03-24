import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createTransaction, getReferences } from '../api/client';
import { useToast } from '../components/Toast';
import { ChevronLeft, AlertTriangle, Check } from 'lucide-react';
import type { References, TransactionCreate } from '../types';

const CATEGORY_EMOJI: Record<string, string> = {
  'Продукты': '🛒', 'Кафе': '☕', 'Транспорт': '🚌', 'Такси': '🚕',
  'Досуг': '🎮', 'Покупки': '🛍️', 'Здоровье и красота': '💅',
  'Аптека': '💊', 'Ништяки': '🍫', 'Аренда': '🏠', 'Коммуналка': '🔌',
  'Интернет и связь': '📱', 'Кошки': '🐱', 'Долги': '💳', 'Одежда': '👕',
  'Подарки': '🎁', 'Зарплата': '💰', 'Чаевые': '💵', 'Подработка': '💼',
};

type Step = 'type' | 'date' | 'account' | 'to_account' | 'category' | 'currency' | 'amount' | 'exchange_rate' | 'hours' | 'comment' | 'confirm';

function formatDate(d: Date): string {
  return d.toISOString().split('T')[0];
}

function dayLabel(d: Date): string {
  return `${d.getDate()}.${String(d.getMonth() + 1).padStart(2, '0')}.${d.getFullYear()}`;
}

export default function AddTransactionPage() {
  const navigate = useNavigate();
  const { showToast } = useToast();
  const [refs, setRefs] = useState<References | null>(null);
  const [step, setStep] = useState<Step>('type');
  const [data, setData] = useState<Partial<TransactionCreate>>({ currency: 'BYN' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [customDay, setCustomDay] = useState('');

  useEffect(() => {
    getReferences().then(setRefs).catch((e) => setError(e.message || 'Не удалось загрузить данные'));
  }, []);

  const stepOrder: Step[] = ['type', 'date', 'account', 'to_account', 'category', 'currency', 'amount', 'exchange_rate', 'hours', 'comment', 'confirm'];
  const goBack = () => {
    const idx = stepOrder.indexOf(step);
    if (idx <= 0) { navigate('/'); return; }
    for (let i = idx - 1; i >= 0; i--) {
      const prev = stepOrder[i];
      if (prev === 'to_account' && data.type !== 'Перевод' && data.type !== 'Обмен валюты') continue;
      if (prev === 'category' && (data.type === 'Перевод')) continue;
      if (prev === 'currency' && data.type !== 'Обмен валюты') continue;
      if (prev === 'exchange_rate' && data.type !== 'Обмен валюты') continue;
      if (prev === 'hours' && !(data.type === 'Доход' && (data.category === 'Зарплата' || data.category === 'Чаевые'))) continue;
      setStep(prev);
      return;
    }
    navigate('/');
  };

  const haptic = () => window.Telegram?.WebApp?.HapticFeedback?.selectionChanged();

  const reset = () => {
    setData({ currency: 'BYN' });
    setStep('type');
    setCustomDay('');
  };

  const selectType = (type: string) => { haptic(); setData({ ...data, type }); setStep('date'); };

  const selectDate = (dateStr: string) => { haptic(); setData({ ...data, date: dateStr }); setStep('account'); };

  const submitCustomDate = () => {
    const day = parseInt(customDay);
    if (!day || day < 1) return;
    const now = new Date();
    const maxDay = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate();
    if (day > maxDay) return;
    const d = new Date(now.getFullYear(), now.getMonth(), day);
    selectDate(formatDate(d));
  };

  const selectAccount = (account: string) => {
    haptic();
    setData({ ...data, account });
    if (data.type === 'Перевод' || data.type === 'Обмен валюты') {
      setStep('to_account');
    } else {
      setStep('category');
    }
  };

  const selectToAccount = (to_account: string) => {
    haptic();
    setData({ ...data, to_account });
    setStep(data.type === 'Обмен валюты' ? 'currency' : 'amount');
  };

  const selectCategory = (category: string) => { haptic(); setData({ ...data, category }); setStep('amount'); };

  const selectCurrency = (currency: string) => { haptic(); setData({ ...data, currency }); setStep('amount'); };

  const afterAmount = () => {
    if (data.type === 'Обмен валюты') setStep('exchange_rate');
    else if (data.type === 'Доход' && (data.category === 'Зарплата' || data.category === 'Чаевые')) setStep('hours');
    else setStep('comment');
  };

  const afterExchangeRate = () => setStep('comment');
  const afterHours = () => setStep('comment');

  const handleSubmit = async () => {
    if (!data.type || !data.account || !data.amount || loading) return;
    setLoading(true);
    setError('');
    try {
      await createTransaction(data as TransactionCreate);
      window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('success');
      showToast('Транзакция сохранена', 'success');
      navigate('/');
    } catch (e) {
      window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('error');
      setError(e instanceof Error ? e.message : 'Ошибка сохранения');
      showToast('Ошибка сохранения', 'error');
    } finally {
      setLoading(false);
    }
  };

  const today = new Date();
  const yesterday = new Date(today); yesterday.setDate(today.getDate() - 1);
  const dayBefore = new Date(today); dayBefore.setDate(today.getDate() - 2);

  const currentCategories = data.type === 'Доход'
    ? (refs?.income_categories || [])
    : (refs?.categories || []);

  const exchangeAmount = (data.amount && data.exchange_rate)
    ? (data.amount * data.exchange_rate).toFixed(2)
    : null;

  // Step progress indicator
  const totalSteps = stepOrder.filter((s) => {
    if (s === 'to_account' && data.type !== 'Перевод' && data.type !== 'Обмен валюты') return false;
    if (s === 'category' && data.type === 'Перевод') return false;
    if (s === 'currency' && data.type !== 'Обмен валюты') return false;
    if (s === 'exchange_rate' && data.type !== 'Обмен валюты') return false;
    if (s === 'hours' && !(data.type === 'Доход' && (data.category === 'Зарплата' || data.category === 'Чаевые'))) return false;
    return true;
  }).length;
  const currentStepIdx = stepOrder.slice(0, stepOrder.indexOf(step) + 1).filter((s) => {
    if (s === 'to_account' && data.type !== 'Перевод' && data.type !== 'Обмен валюты') return false;
    if (s === 'category' && data.type === 'Перевод') return false;
    if (s === 'currency' && data.type !== 'Обмен валюты') return false;
    if (s === 'exchange_rate' && data.type !== 'Обмен валюты') return false;
    if (s === 'hours' && !(data.type === 'Доход' && (data.category === 'Зарплата' || data.category === 'Чаевые'))) return false;
    return true;
  }).length;
  const progressPct = totalSteps > 0 ? (currentStepIdx / totalSteps) * 100 : 0;

  if (error && !refs) return (
    <div className="page">
      <div className="error-box" role="alert">
        <AlertTriangle size={48} color="var(--danger)" />
        <div className="error-text">{error}</div>
        <button className="btn btn-primary" onClick={() => window.location.reload()}>Повторить</button>
      </div>
    </div>
  );

  return (
    <div className="page">
      {/* R7: Progress bar at top */}
      <div className="progress-bar" style={{ marginBottom: 12, height: 4 }}
        role="progressbar" aria-valuenow={Math.round(progressPct)} aria-valuemin={0} aria-valuemax={100}
        aria-label={`Шаг ${currentStepIdx} из ${totalSteps}`}>
        <div className="progress-fill ok" style={{ width: `${progressPct}%`, background: 'linear-gradient(90deg, var(--accent), var(--success))' }} />
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
        {step !== 'type' && (
          <button className="btn btn-ghost" onClick={goBack} style={{ padding: '4px 12px', fontSize: 14 }} aria-label="Назад">
            <ChevronLeft size={16} /> Назад
          </button>
        )}
        <h1 className="page-title" style={{ margin: 0 }}>Новая транзакция</h1>
      </div>

      {error && (
        <div className="warning-card danger" role="alert" style={{ marginBottom: 12 }}>
          <AlertTriangle size={16} />
          <span>{error}</span>
        </div>
      )}

      {/* Step: Type */}
      {step === 'type' && (
        <div className="card">
          <div className="card-title">Тип</div>
          <div className="grid-2">
            {['Расход', 'Доход', 'Перевод', 'Обмен валюты'].map((t) => (
              <button key={t} className="btn btn-ghost btn-full" onClick={() => selectType(t)}>
                {t === 'Расход' ? '💸' : t === 'Доход' ? '💰' : t === 'Перевод' ? '🔄' : '💱'} {t}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Step: Date */}
      {step === 'date' && (
        <div className="card">
          <div className="card-title">Дата</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            <button className="btn btn-ghost btn-full" onClick={() => selectDate(formatDate(today))}>
              Сегодня ({dayLabel(today)})
            </button>
            <button className="btn btn-ghost btn-full" onClick={() => selectDate(formatDate(yesterday))}>
              Вчера ({dayLabel(yesterday)})
            </button>
            <button className="btn btn-ghost btn-full" onClick={() => selectDate(formatDate(dayBefore))}>
              Позавчера ({dayLabel(dayBefore)})
            </button>
            <div style={{ display: 'flex', gap: 8, marginTop: 4 }}>
              <input
                type="number"
                inputMode="numeric"
                placeholder="Число месяца (1-31)"
                value={customDay}
                onChange={(e) => setCustomDay(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && submitCustomDate()}
                aria-label="Число месяца"
                style={{
                  flex: 1, padding: '10px', fontSize: 15,
                  background: 'var(--bg-secondary)', color: 'var(--text-primary)',
                  border: '1px solid var(--border)', borderRadius: 10,
                }}
              />
              <button className="btn btn-primary" onClick={submitCustomDate}>OK</button>
            </div>
          </div>
        </div>
      )}

      {/* Step: Account */}
      {step === 'account' && refs && (
        <div className="card">
          <div className="card-title">{data.type === 'Перевод' || data.type === 'Обмен валюты' ? 'Откуда' : 'Счёт'}</div>
          {refs.accounts.map((acc) => (
            <button key={acc} className="btn btn-ghost btn-full" style={{ marginBottom: 8 }}
              onClick={() => selectAccount(acc)}>
              {acc}
            </button>
          ))}
        </div>
      )}

      {/* Step: To Account */}
      {step === 'to_account' && refs && (
        <div className="card">
          <div className="card-title">Куда</div>
          {refs.accounts
            .filter((acc) => acc !== data.account)
            .map((acc) => (
              <button key={acc} className="btn btn-ghost btn-full" style={{ marginBottom: 8 }}
                onClick={() => selectToAccount(acc)}>
                {acc}
              </button>
            ))}
        </div>
      )}

      {/* Step: Category */}
      {step === 'category' && (
        <div className="card">
          <div className="card-title">Категория</div>
          <div className="grid-2">
            {currentCategories.map((cat) => (
              <button key={cat} className="btn btn-ghost" onClick={() => selectCategory(cat)}>
                {CATEGORY_EMOJI[cat] || '📦'} {cat}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Step: Currency (exchange only) */}
      {step === 'currency' && (
        <div className="card">
          <div className="card-title">Валюта (что отдаёте)</div>
          <div className="grid-2">
            {['USD', 'EUR', 'RUB', 'BYN'].map((c) => (
              <button key={c} className="btn btn-ghost" onClick={() => selectCurrency(c)}>
                {c === 'USD' ? '🇺🇸' : c === 'EUR' ? '🇪🇺' : c === 'RUB' ? '🇷🇺' : '🇧🇾'} {c}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Step: Amount */}
      {step === 'amount' && (
        <div className="card">
          <div className="card-title">Сумма {data.currency && data.currency !== 'BYN' ? `(${data.currency})` : '(BYN)'}</div>
          <input
            type="number"
            inputMode="decimal"
            autoFocus
            placeholder="0.00"
            aria-label="Сумма"
            style={{
              width: '100%', padding: '12px', fontSize: 24, fontWeight: 700,
              background: 'var(--bg-secondary)', color: 'var(--text-primary)',
              border: '1px solid var(--border)', borderRadius: 10, textAlign: 'center',
            }}
            onChange={(e) => setData({ ...data, amount: parseFloat(e.target.value) || 0 })}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && data.amount) afterAmount();
            }}
          />
          <button className="btn btn-primary btn-full" style={{ marginTop: 12 }}
            onClick={() => data.amount && afterAmount()}
            disabled={!data.amount}>
            Далее
          </button>
        </div>
      )}

      {/* Step: Exchange Rate */}
      {step === 'exchange_rate' && (
        <div className="card">
          <div className="card-title">Курс ({data.currency} → BYN)</div>
          <input
            type="number"
            inputMode="decimal"
            autoFocus
            placeholder="Курс обмена"
            aria-label="Курс обмена"
            style={{
              width: '100%', padding: '12px', fontSize: 24, fontWeight: 700,
              background: 'var(--bg-secondary)', color: 'var(--text-primary)',
              border: '1px solid var(--border)', borderRadius: 10, textAlign: 'center',
            }}
            onChange={(e) => {
              const rate = parseFloat(e.target.value) || 0;
              const amount_to = data.amount ? parseFloat((data.amount * rate).toFixed(2)) : 0;
              setData({ ...data, exchange_rate: rate, amount_to });
            }}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && data.exchange_rate) afterExchangeRate();
            }}
          />
          {exchangeAmount && (
            <div style={{ marginTop: 8, textAlign: 'center', color: 'var(--text-secondary)' }}>
              {data.amount} {data.currency} = <strong>{exchangeAmount} BYN</strong>
            </div>
          )}
          <button className="btn btn-primary btn-full" style={{ marginTop: 12 }}
            onClick={() => data.exchange_rate && afterExchangeRate()}
            disabled={!data.exchange_rate}>
            Далее
          </button>
        </div>
      )}

      {/* Step: Hours */}
      {step === 'hours' && (
        <div className="card">
          <div className="card-title">Часы работы</div>
          <input
            type="number"
            inputMode="decimal"
            autoFocus
            placeholder="Сколько часов"
            aria-label="Часы работы"
            style={{
              width: '100%', padding: '12px', fontSize: 24, fontWeight: 700,
              background: 'var(--bg-secondary)', color: 'var(--text-primary)',
              border: '1px solid var(--border)', borderRadius: 10, textAlign: 'center',
            }}
            onChange={(e) => setData({ ...data, hours: parseFloat(e.target.value) || 0 })}
            onKeyDown={(e) => {
              if (e.key === 'Enter') afterHours();
            }}
          />
          <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
            <button className="btn btn-ghost" style={{ flex: 1 }} onClick={afterHours}>
              Пропустить
            </button>
            <button className="btn btn-primary" style={{ flex: 1 }} onClick={afterHours}>
              Далее
            </button>
          </div>
        </div>
      )}

      {/* Step: Comment */}
      {step === 'comment' && (
        <div className="card">
          <div className="card-title">Комментарий (необязательно)</div>
          <input
            type="text"
            autoFocus
            placeholder="Описание..."
            aria-label="Комментарий к транзакции"
            style={{
              width: '100%', padding: '12px', fontSize: 16,
              background: 'var(--bg-secondary)', color: 'var(--text-primary)',
              border: '1px solid var(--border)', borderRadius: 10,
            }}
            onChange={(e) => setData({ ...data, comment: e.target.value })}
            onKeyDown={(e) => {
              if (e.key === 'Enter') setStep('confirm');
            }}
          />
          <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
            <button className="btn btn-ghost" style={{ flex: 1 }}
              onClick={() => setStep('confirm')}>
              Пропустить
            </button>
            <button className="btn btn-primary" style={{ flex: 1 }}
              onClick={() => setStep('confirm')}>
              Далее
            </button>
          </div>
        </div>
      )}

      {/* Step: Confirm */}
      {step === 'confirm' && (
        <div className="card">
          <div className="card-title">Подтверждение</div>
          <div style={{ marginBottom: 16, lineHeight: 1.8 }}>
            <div><strong>Тип:</strong> {data.type}</div>
            <div><strong>Дата:</strong> {data.date}</div>
            <div><strong>Счёт:</strong> {data.account}</div>
            {data.to_account && <div><strong>Куда:</strong> {data.to_account}</div>}
            {data.category && <div><strong>Категория:</strong> {CATEGORY_EMOJI[data.category] || ''} {data.category}</div>}
            <div><strong>Сумма:</strong> {data.amount} {data.currency || 'BYN'}</div>
            {data.exchange_rate && <div><strong>Курс:</strong> {data.exchange_rate}</div>}
            {data.amount_to && <div><strong>Итого BYN:</strong> {data.amount_to}</div>}
            {data.hours && <div><strong>Часы:</strong> {data.hours}</div>}
            {data.comment && <div><strong>Комментарий:</strong> {data.comment}</div>}
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn btn-ghost" style={{ flex: 1 }} onClick={reset}>
              Отмена
            </button>
            <button className="btn btn-primary" style={{ flex: 1 }}
              onClick={handleSubmit} disabled={loading}>
              <Check size={16} />
              {loading ? 'Сохранение...' : 'Сохранить'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
