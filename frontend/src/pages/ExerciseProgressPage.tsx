import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getCurrentWeights, getExerciseProgress } from '../api/client';
import type { ExerciseWeight, ExerciseProgress } from '../types';

const TREND_ICON: Record<string, string> = {
  up: '📈',
  down: '📉',
  stable: '➡️',
  no_data: '—',
};

export default function ExerciseProgressPage() {
  const navigate = useNavigate();
  const [weights, setWeights] = useState<ExerciseWeight[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selected, setSelected] = useState<string | null>(null);
  const [progress, setProgress] = useState<ExerciseProgress | null>(null);
  const [progressLoading, setProgressLoading] = useState(false);

  const load = () => {
    setLoading(true); setError('');
    getCurrentWeights()
      .then(setWeights)
      .catch((e) => setError(e.message || 'Ошибка загрузки'))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const showProgress = async (exerciseId: string) => {
    if (selected === exerciseId) {
      setSelected(null);
      setProgress(null);
      return;
    }
    setSelected(exerciseId);
    setProgressLoading(true);
    try {
      const p = await getExerciseProgress(exerciseId);
      setProgress(p);
    } catch {
      setProgress(null);
    } finally {
      setProgressLoading(false);
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
        <h1 className="page-title" style={{ margin: 0 }}>Прогресс упражнений</h1>
      </div>

      {weights.length === 0 ? (
        <div className="empty">
          <div className="empty-icon">📊</div>
          Нет данных
        </div>
      ) : (
        ['A', 'B'].map((day) => {
          const dayWeights = weights.filter((w) => w.day === day);
          if (dayWeights.length === 0) return null;
          return (
            <div key={day}>
              <h2 style={{ fontSize: 16, marginBottom: 8, marginTop: 12 }}>День {day}</h2>
              <div className="card" style={{ padding: 0 }}>
                {dayWeights.map((w) => (
                  <div key={w.exercise_id}>
                    <div className="list-item" style={{ cursor: 'pointer' }}
                      onClick={() => showProgress(w.exercise_id)}>
                      <div className="list-item-content">
                        <div className="list-item-title">{w.name}</div>
                        <div className="list-item-meta">
                          {w.category} · {w.target_reps}
                          {w.status === 'ready' && ' · ✅ Готов к увеличению'}
                        </div>
                      </div>
                      <div className="list-item-right">
                        <div className="amount">{w.current_weight} кг</div>
                        <div className="stat-label">{selected === w.exercise_id ? '▲' : '▼'}</div>
                      </div>
                    </div>

                    {/* Expanded progress */}
                    {selected === w.exercise_id && (
                      <div style={{ padding: '0 12px 12px', background: 'var(--bg-card-hover)' }}>
                        {progressLoading ? (
                          <div style={{ padding: 12, color: 'var(--text-muted)', textAlign: 'center' }}>Загрузка...</div>
                        ) : progress ? (
                          <>
                            <div style={{ display: 'flex', gap: 16, marginBottom: 8, fontSize: 13 }}>
                              <span>Тренд: {TREND_ICON[progress.trend]} {progress.trend}</span>
                              <span>Статус: {progress.status}</span>
                            </div>
                            {progress.history_by_workout.length > 0 ? (
                              progress.history_by_workout.slice(0, 5).map((wk, i) => (
                                <div key={i} style={{
                                  padding: '6px 0', borderBottom: '1px solid var(--border)',
                                  fontSize: 13, color: 'var(--text-secondary)',
                                }}>
                                  <div style={{ marginBottom: 2 }}>
                                    <strong>{wk.date}</strong> · День {wk.day_type}
                                  </div>
                                  <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                                    {wk.sets.map((s) => (
                                      <span key={s.set_number} style={{
                                        padding: '2px 6px', borderRadius: 4,
                                        background: 'var(--bg-secondary)', fontSize: 12,
                                      }}>
                                        {s.weight}x{s.reps} RPE:{s.rpe}
                                      </span>
                                    ))}
                                  </div>
                                </div>
                              ))
                            ) : (
                              <div style={{ color: 'var(--text-muted)', fontSize: 13 }}>Нет истории</div>
                            )}
                          </>
                        ) : (
                          <div style={{ color: 'var(--text-muted)', fontSize: 13 }}>Ошибка загрузки</div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          );
        })
      )}
    </div>
  );
}
