import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createTransaction, getReferences } from '../api/client';
import type { References, TransactionCreate } from '../types';

const CATEGORY_EMOJI: Record<string, string> = {
  'Продукты': '🛒', 'Кафе': '☕', 'Транспорт': '🚌', 'Такси': '🚕',
  'Досуг': '🎮', 'Покупки': '🛍️', 'Здоровье и красота': '💅',
  'Аптека': '💊', 'Ништяки': '🍫', 'Аренда': '🏠', 'Коммуналка': '🔌',
  'Интернет и связь': '📱', 'Кошки': '🐱', 'Долги': '💳', 'Одежда': '👕',
  'Подарки': '🎁', 'Зарплата': '💰', 'Чаевые': '💵', 'Подработка': '💼',
};

type Step = 'type' | 'account' | 'category' | 'amount' | 'comment' | 'confirm';

export default function AddTransactionPage() {
  const navigate = useNavigate();
  const [refs, setRefs] = useState<References | null>(null);
  const [step, setStep] = useState<Step>('type');
  const [data, setData] = useState<Partial<TransactionCreate>>({
    day: new Date().getDate(),
    currency: 'BYN',
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getReferences().then(setRefs).catch(() => {});
  }, []);

  const haptic = () => window.Telegram?.WebApp?.HapticFeedback?.selectionChanged();

  const selectType = (type: string) => {
    haptic();
    setData({ ...data, type });
    setStep('account');
  };

  const selectAccount = (account: string) => {
    haptic();
    setData({ ...data, account });
    if (data.type === 'Перевод') {
      // Для перевода нужен to_account — пропускаем категорию
      setStep('amount');
    } else {
      setStep('category');
    }
  };

  const selectCategory = (category: string) => {
    haptic();
    setData({ ...data, category });
    setStep('amount');
  };

  const handleSubmit = async () => {
    if (!data.type || !data.account || !data.amount) return;
    setLoading(true);
    try {
      await createTransaction(data as TransactionCreate);
      window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('success');
      navigate('/');
    } catch {
      window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <h1 className="page-title">Новая транзакция</h1>

      {/* Step: Type */}
      {step === 'type' && (
        <div className="card">
          <div className="card-title">Тип</div>
          <div className="grid-2">
            {['Расход', 'Доход', 'Перевод'].map((t) => (
              <button key={t} className="btn btn-ghost btn-full" onClick={() => selectType(t)}>
                {t === 'Расход' ? '💸' : t === 'Доход' ? '💰' : '🔄'} {t}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Step: Account */}
      {step === 'account' && refs && (
        <div className="card">
          <div className="card-title">Счёт</div>
          {refs.accounts.map((acc) => (
            <button key={acc} className="btn btn-ghost btn-full" style={{ marginBottom: 8 }}
              onClick={() => selectAccount(acc)}>
              {acc}
            </button>
          ))}
        </div>
      )}

      {/* Step: Category */}
      {step === 'category' && refs && (
        <div className="card">
          <div className="card-title">Категория</div>
          <div className="grid-2">
            {refs.categories.map((cat) => (
              <button key={cat} className="btn btn-ghost" onClick={() => selectCategory(cat)}>
                {CATEGORY_EMOJI[cat] || '📦'} {cat}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Step: Amount */}
      {step === 'amount' && (
        <div className="card">
          <div className="card-title">Сумма</div>
          <input
            type="number"
            inputMode="decimal"
            autoFocus
            placeholder="0.00"
            style={{
              width: '100%', padding: '12px', fontSize: 24, fontWeight: 700,
              background: 'var(--bg-secondary)', color: 'var(--text-primary)',
              border: '1px solid var(--border)', borderRadius: 10, textAlign: 'center',
            }}
            onChange={(e) => setData({ ...data, amount: parseFloat(e.target.value) || 0 })}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && data.amount) setStep('comment');
            }}
          />
          <button className="btn btn-primary btn-full" style={{ marginTop: 12 }}
            onClick={() => data.amount && setStep('comment')}
            disabled={!data.amount}>
            Далее
          </button>
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
          <div style={{ marginBottom: 16 }}>
            <div><strong>Тип:</strong> {data.type}</div>
            <div><strong>Счёт:</strong> {data.account}</div>
            {data.category && <div><strong>Категория:</strong> {data.category}</div>}
            <div><strong>Сумма:</strong> {data.amount} {data.currency}</div>
            {data.comment && <div><strong>Комментарий:</strong> {data.comment}</div>}
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn btn-ghost" style={{ flex: 1 }}
              onClick={() => { setStep('type'); setData({ day: new Date().getDate(), currency: 'BYN' }); }}>
              Отмена
            </button>
            <button className="btn btn-primary" style={{ flex: 1 }}
              onClick={handleSubmit} disabled={loading}>
              {loading ? 'Сохранение...' : 'Сохранить'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
