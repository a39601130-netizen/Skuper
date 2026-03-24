import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getCurrentWeights, getExerciseProgress } from '../api/client';
import { ListPageSkeleton } from '../components/Skeleton';
import { ChevronLeft, AlertTriangle, BarChart3, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import type { ExerciseWeight, ExerciseProgress } from '../types';

const TREND_ICON: Record<string, typeof TrendingUp> = {
  up: TrendingUp,
  down: TrendingDown,
  stable: Minus,
};

const TREND_COLOR: Record<string, string> = {
  up: 'var(--success)',
  down: 'var(--danger)',
  stable: 'var(--text-muted)',
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
    setProgress(null);
    try {
      const p = await getExerciseProgress(exerciseId);
      setSelected((current) => {
        if (current === exerciseId) {
          setProgress(p);
        }
        return current;
      });
    } catch {
      setProgress(null);
    } finally {
      setProgressLoading(false);
    }
  };

  if (loading) return <ListPageSkeleton />;
  if (error) return (
    <div className="page workout-ctx">
      <div className="error-box" role="alert">
        <AlertTriangle size={48} color="var(--danger)" />
        <div className="error-text">{error}</div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-ghost" onClick={() => navigate(-1)} aria-label="Назад">
            <ChevronLeft size={16} /> Назад
          </button>
          <button className="btn btn-primary" onClick={load}>Повторить</button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="page workout-ctx">
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
        <button className="btn btn-ghost" onClick={() => navigate(-1)} style={{ padding: '4px 12px', fontSize: 14 }} aria-label="Назад">
          <ChevronLeft size={16} /> Назад
        </button>
        <div className="page-title-bar" style={{ margin: 0 }}>
          <h1 className="page-title" style={{ margin: 0 }}>Прогресс упражнений</h1>
        </div>
      </div>

      {weights.length === 0 ? (
        <div className="empty">
          <div className="empty-icon"><BarChart3 size={48} /></div>
          <div className="empty-text">Нет данных</div>
          <div className="empty-hint">Завершите хотя бы одну тренировку для отслеживания прогресса</div>
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
                      onClick={() => showProgress(w.exercise_id)}
                      role="button"
                      aria-expanded={selected === w.exercise_id}
                      aria-label={`Показать прогресс ${w.name}`}
                    >
                      <div className="list-item-content">
                        <div className="list-item-title">{w.name}</div>
                        <div className="list-item-meta">
                          {w.category} · {w.target_reps}
                          {w.status === 'ready' && ' · ✅ Готов к увеличению'}
                        </div>
                      </div>
                      <div className="list-item-right">
                        <div className="amount" style={{ color: 'var(--workout-accent)' }}>{w.current_weight} кг</div>
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
                            <div style={{ display: 'flex', gap: 16, marginBottom: 8, fontSize: 13, alignItems: 'center' }}>
                              <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                                Тренд: {(() => {
                                  const Icon = TREND_ICON[progress.trend];
                                  return Icon ? <Icon size={14} color={TREND_COLOR[progress.trend]} /> : '—';
                                })()}
                                <span style={{ color: TREND_COLOR[progress.trend] }}>{progress.trend}</span>
                              </span>
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
