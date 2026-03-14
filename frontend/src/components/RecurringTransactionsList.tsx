import { useEffect, useState } from 'react';
import {
  getRecurringTransactions, createRecurringTransaction,
  deleteRecurringTransaction, applyRecurringTransaction, getReferences,
} from '../api/client';
import type { RecurringTransaction, RecurringTransactionCreate, References } from '../types';

const FREQ_LABELS: Record<string, string> = {
  daily: 'Ежедневно',
  weekly: 'Еженедельно',
  monthly: 'Ежемесячно',
};

export default function RecurringTransactionsList() {
  const [items, setItems] = useState<RecurringTransaction[]>([]);
  const [refs, setRefs] = useState<References | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<Partial<RecurringTransactionCreate>>({
    frequency: 'monthly',
    currency: 'BYN',
  });

  const load = () => {
    getRecurringTransactions().then(setItems).catch(() => {});
  };

  useEffect(() => {
    load();
    getReferences().then(setRefs).catch(() => {});
  }, []);

  const handleCreate = async () => {
    if (!form.name || !form.type || !form.account || !form.amount || !form.next_date) return;
    try {
      await createRecurringTransaction(form as RecurringTransactionCreate);
      setShowForm(false);
      setForm({ frequency: 'monthly', currency: 'BYN' });
      load();
    } catch { /* ignore */ }
  };

  const handleApply = async (id: number) => {
    try {
      await applyRecurringTransaction(id);
      window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('success');
      load();
    } catch {
      window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('error');
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Удалить?')) return;
    await deleteRecurringTransaction(id);
    load();
  };

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div className="card-title">Повторяющиеся</div>
        <button className="btn btn-ghost" style={{ fontSize: 12, padding: '4px 8px' }}
          onClick={() => setShowForm(!showForm)}>
          {showForm ? 'Отмена' : '+ Добавить'}
        </button>
      </div>

      {showForm && refs && (
        <div style={{ marginBottom: 12, padding: 12, background: 'var(--bg-secondary)', borderRadius: 8 }}>
          <input placeholder="Название" value={form.name || ''}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            style={inputStyle} />
          <select value={form.type || ''} onChange={(e) => setForm({ ...form, type: e.target.value })}
            style={inputStyle}>
            <option value="">Тип</option>
            <option value="Расход">Расход</option>
            <option value="Доход">Доход</option>
          </select>
          <select value={form.account || ''} onChange={(e) => setForm({ ...form, account: e.target.value })}
            style={inputStyle}>
            <option value="">Счёт</option>
            {refs.accounts.map((a) => <option key={a} value={a}>{a}</option>)}
          </select>
          <select value={form.category || ''} onChange={(e) => setForm({ ...form, category: e.target.value })}
            style={inputStyle}>
            <option value="">Категория</option>
            {refs.categories.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
          <input type="number" placeholder="Сумма" value={form.amount || ''}
            onChange={(e) => setForm({ ...form, amount: parseFloat(e.target.value) || 0 })}
            style={inputStyle} />
          <select value={form.frequency || 'monthly'}
            onChange={(e) => setForm({ ...form, frequency: e.target.value })}
            style={inputStyle}>
            <option value="daily">Ежедневно</option>
            <option value="weekly">Еженедельно</option>
            <option value="monthly">Ежемесячно</option>
          </select>
          <input type="date" value={form.next_date || ''}
            onChange={(e) => setForm({ ...form, next_date: e.target.value })}
            style={inputStyle} />
          <button className="btn btn-primary btn-full" style={{ marginTop: 8 }} onClick={handleCreate}>
            Создать
          </button>
        </div>
      )}

      {items.length === 0 && !showForm && (
        <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Нет повторяющихся транзакций</div>
      )}

      {items.map((rt) => (
        <div className="list-item" key={rt.id}>
          <div className="list-item-content">
            <div className="list-item-title">{rt.name}</div>
            <div className="list-item-meta">
              {rt.amount} {rt.currency} · {FREQ_LABELS[rt.frequency] || rt.frequency} · След: {rt.next_date}
            </div>
          </div>
          <div style={{ display: 'flex', gap: 4 }}>
            <button className="btn btn-ghost" style={{ fontSize: 11, padding: '4px 8px' }}
              onClick={() => handleApply(rt.id)}>
              Применить
            </button>
            <button style={{
              background: 'none', border: 'none', color: 'var(--danger)',
              fontSize: 11, cursor: 'pointer', padding: '4px',
            }} onClick={() => handleDelete(rt.id)}>
              ✕
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}

const inputStyle: React.CSSProperties = {
  width: '100%', padding: '8px', fontSize: 13, marginBottom: 6,
  background: 'var(--bg-primary)', color: 'var(--text-primary)',
  border: '1px solid var(--border)', borderRadius: 6,
};
