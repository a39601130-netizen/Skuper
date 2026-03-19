import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getWorkoutHistory, deleteWorkout2 } from '../api/client';
import type { WorkoutHistory } from '../types';

export default function WorkoutHistoryPage() {
  const navigate = useNavigate();
  const [history, setHistory] = useState<WorkoutHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [confirmId, setConfirmId] = useState<number | null>(null);

  const load = () => {
    setLoading(true); setError('');
    getWorkoutHistory(20)
      .then(setHistory)
      .catch((e) => setError(e.message || 'Ошибка загрузки'))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const handleDelete = async (id: number) => {
    try {
      await deleteWorkout2(id);
      setHistory((prev) => prev.filter((w) => w.id !== id));
      setConfirmId(null);
      window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('success');
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Ошибка удаления';
      setError(msg);
      setConfirmId(null);
    }
  };

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

  return (
    <div className="page">
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
        <button className="btn btn-ghost" onClick={() => navigate(-1)} style={{ padding: '4px 12px', fontSize: 14 }}>← Назад</button>
        <h1 className="page-title" style={{ margin: 0 }}>История тренировок</h1>
      </div>

      {history.length === 0 ? (
        <div className="empty">
          <div className="empty-icon">🏋️</div>
          Нет записей о тренировках
        </div>
      ) : (
        <div className="card" style={{ padding: 0 }}>
          {history.map((w) => (
            <div className="list-item" key={w.id} style={{ flexDirection: 'column', alignItems: 'stretch', position: 'relative' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                <span style={{ fontWeight: 600 }}>
                  День {w.day_type} · Неделя {w.week}
                </span>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span className="stat-label">{w.date}</span>
                  {confirmId === w.id ? (
                    <div style={{ display: 'flex', gap: 4 }}>
                      <button
                        onClick={() => handleDelete(w.id)}
                        style={{
                          background: 'var(--danger)', color: 'white', border: 'none',
                          borderRadius: 6, padding: '2px 8px', fontSize: 12, cursor: 'pointer',
                        }}
                      >Да</button>
                      <button
                        onClick={() => setConfirmId(null)}
                        style={{
                          background: 'var(--bg-secondary)', color: 'var(--text-secondary)', border: 'none',
                          borderRadius: 6, padding: '2px 8px', fontSize: 12, cursor: 'pointer',
                        }}
                      >Нет</button>
                    </div>
                  ) : (
                    <button
                      onClick={() => setConfirmId(w.id)}
                      style={{
                        background: 'none', border: 'none', color: 'var(--text-muted)',
                        cursor: 'pointer', padding: '0 4px', fontSize: 16, lineHeight: 1,
                      }}
                      title="Удалить"
                    >✕</button>
                  )}
                </div>
              </div>
              <div style={{ display: 'flex', gap: 12, fontSize: 13, color: 'var(--text-secondary)', flexWrap: 'wrap' }}>
                <span>Фаза: {w.phase}</span>
                {w.energy_before > 0 && <span>⚡ {w.energy_before}→{w.energy_after}</span>}
                {w.sleep_hours > 0 && <span>😴 {w.sleep_hours}ч</span>}
                {w.sleep_quality && <span>💤 {w.sleep_quality}</span>}
                {w.back_pain && <span>🔙 {w.back_pain}</span>}
                {w.emotional_wave && <span>🌊 {w.emotional_wave}</span>}
              </div>
              {w.notes && (
                <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
                  {w.notes}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
