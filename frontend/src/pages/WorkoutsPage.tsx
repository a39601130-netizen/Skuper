import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getCurrentWeights, getNextWorkout } from '../api/client';
import type { ExerciseWeight, NextWorkout } from '../types';

export default function WorkoutsPage() {
  const navigate = useNavigate();
  const [weights, setWeights] = useState<ExerciseWeight[]>([]);
  const [next, setNext] = useState<NextWorkout | null>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<'next' | 'weights'>('next');

  const [error, setError] = useState('');

  const load = () => {
    setLoading(true); setError('');
    Promise.all([getCurrentWeights(), getNextWorkout()])
      .then(([w, n]) => { setWeights(w); setNext(n); })
      .catch((e) => setError(e.message || 'Ошибка загрузки'))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  if (loading) return <div className="page"><div className="loading">Загрузка...</div></div>;
  if (error) return (
    <div className="page">
      <div className="error-box">
        <div className="error-icon">⚠️</div>
        <div className="error-text">{error}</div>
        <button className="btn btn-primary" onClick={load}>Повторить</button>
      </div>
    </div>
  );

  return (
    <div className="page">
      <h1 className="page-title">Тренировки</h1>

      {/* Quick links */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
        <button className="btn btn-ghost" style={{ flex: 1, fontSize: 13 }}
          onClick={() => navigate('/workout-history')}>
          📜 История
        </button>
        <button className="btn btn-ghost" style={{ flex: 1, fontSize: 13 }}
          onClick={() => navigate('/exercise-progress')}>
          📊 Прогресс
        </button>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        <button className={`btn ${tab === 'next' ? 'btn-primary' : 'btn-ghost'}`}
          onClick={() => setTab('next')}>
          Следующая
        </button>
        <button className={`btn ${tab === 'weights' ? 'btn-primary' : 'btn-ghost'}`}
          onClick={() => setTab('weights')}>
          Веса
        </button>
      </div>

      {/* Next Workout */}
      {tab === 'next' && !next && (
        <div className="empty"><div className="empty-icon">🏋️</div>Нет данных о следующей тренировке</div>
      )}
      {tab === 'next' && next && (
        <>
          <div className="card">
            <div className="card-title">Следующая тренировка</div>
            <div style={{ fontSize: 18, fontWeight: 600, marginBottom: 4 }}>
              День {next.next_day}
            </div>
            {next.phase && (
              <div className="stat-label">
                Фаза: {next.phase.phase_name || '—'} · Неделя {next.phase.current_week || '?'}
                {next.phase.rpe_min > 0 && ` · RPE ${next.phase.rpe_min}-${next.phase.rpe_max}`}
              </div>
            )}
          </div>

          <div className="card" style={{ padding: 0 }}>
            {next.exercises.map((ex) => (
              <div className="list-item" key={ex.exercise_id} style={{ flexWrap: 'wrap' }}>
                <span className="list-item-icon">🏋️</span>
                <div className="list-item-content">
                  <div className="list-item-title">{ex.name}</div>
                  <div className="list-item-meta">{ex.category}</div>
                </div>
                <div className="list-item-right">
                  <div className="amount">{ex.current_weight || 0} кг</div>
                  <div className="stat-label">{ex.target_reps || ''}</div>
                </div>
                {ex.notes && (
                  <div style={{ width: '100%', padding: '4px 0 2px 36px', fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                    💡 {ex.notes}
                  </div>
                )}
              </div>
            ))}
          </div>

          <button className="btn btn-primary" style={{ width: '100%', marginTop: 16, padding: '14px 0', fontSize: 16 }}
            onClick={() => navigate('/workout/session')}>
            💪 Начать тренировку
          </button>
        </>
      )}

      {/* Current Weights */}
      {tab === 'weights' && weights.length === 0 && (
        <div className="empty"><div className="empty-icon">📊</div>Нет данных о весах</div>
      )}
      {tab === 'weights' && weights.length > 0 && (
        <>
          {['A', 'B'].map((day) => {
            const dayWeights = weights.filter((w) => w.day === day);
            if (dayWeights.length === 0) return null;
            return (
              <div key={day}>
                <h2 style={{ fontSize: 16, marginBottom: 8, marginTop: 8 }}>День {day}</h2>
                <div className="card" style={{ padding: 0 }}>
                  {dayWeights.map((w) => (
                    <div className="list-item" key={w.exercise_id}>
                      <div className="list-item-content">
                        <div className="list-item-title">{w.name}</div>
                        <div className="list-item-meta">
                          {w.status === 'ready' ? '✅ Готов к увеличению' : w.target_reps}
                        </div>
                      </div>
                      <div className="list-item-right">
                        <div className="amount">{w.current_weight} кг</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </>
      )}
    </div>
  );
}
