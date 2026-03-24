import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getWorkoutHistory, deleteWorkout, getWorkout } from '../api/client';
import { ListPageSkeleton } from '../components/Skeleton';
import { useToast } from '../components/Toast';
import { ChevronLeft, ChevronDown, ChevronUp, AlertTriangle, Dumbbell } from 'lucide-react';
import type { WorkoutHistory, WorkoutSetData } from '../types';

interface WorkoutDetails {
  sets: WorkoutSetData[];
}

export default function WorkoutHistoryPage() {
  const navigate = useNavigate();
  const { showToast } = useToast();
  const [history, setHistory] = useState<WorkoutHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [confirmId, setConfirmId] = useState<number | null>(null);
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [details, setDetails] = useState<Record<number, WorkoutDetails>>({});
  const [loadingDetails, setLoadingDetails] = useState<number | null>(null);

  const load = () => {
    setLoading(true); setError('');
    getWorkoutHistory(20)
      .then(setHistory)
      .catch((e) => setError(e.message || 'Ошибка загрузки'))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const toggleExpand = async (id: number) => {
    if (expandedId === id) {
      setExpandedId(null);
      return;
    }
    setExpandedId(id);
    if (!details[id]) {
      setLoadingDetails(id);
      try {
        const data = await getWorkout(id);
        setDetails((prev) => ({ ...prev, [id]: { sets: data.sets } }));
      } catch {
        showToast('Не удалось загрузить детали', 'error');
      } finally {
        setLoadingDetails(null);
      }
    }
    window.Telegram?.WebApp?.HapticFeedback?.selectionChanged();
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteWorkout(id);
      setHistory((prev) => prev.filter((w) => w.id !== id));
      setConfirmId(null);
      if (expandedId === id) setExpandedId(null);
      window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('success');
      showToast('Тренировка удалена', 'success');
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Ошибка удаления';
      setError(msg);
      setConfirmId(null);
      showToast(msg, 'error');
    }
  };

  // Группируем подходы по упражнениям
  const groupSetsByExercise = (sets: WorkoutSetData[]) => {
    const groups: { name: string; sets: WorkoutSetData[] }[] = [];
    let currentName = '';
    for (const s of sets) {
      const name = s.exercise_name || s.exercise_id || '?';
      if (name !== currentName) {
        groups.push({ name, sets: [s] });
        currentName = name;
      } else {
        groups[groups.length - 1].sets.push(s);
      }
    }
    return groups;
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
          <h1 className="page-title" style={{ margin: 0 }}>История тренировок</h1>
        </div>
      </div>

      {history.length === 0 ? (
        <div className="empty">
          <div className="empty-icon"><Dumbbell size={48} /></div>
          <div className="empty-text">Нет записей о тренировках</div>
          <div className="empty-hint">Начните первую тренировку и она появится здесь</div>
          <button className="empty-action" onClick={() => navigate('/workout/session')} style={{ background: 'var(--workout-accent)' }}>
            Начать тренировку
          </button>
        </div>
      ) : (
        <div className="card" style={{ padding: 0 }}>
          {history.map((w) => {
            const isExpanded = expandedId === w.id;
            const isLoadingThis = loadingDetails === w.id;
            const wDetails = details[w.id];

            return (
              <div key={w.id} className="list-item" style={{ flexDirection: 'column', alignItems: 'stretch', position: 'relative', cursor: 'pointer' }}>
                {/* Header — кликабельный */}
                <div onClick={() => toggleExpand(w.id)}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                    <span style={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: 4 }}>
                      {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                      День {w.day_type} · Неделя {w.week}
                    </span>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span className="stat-label">{w.date}</span>
                      {confirmId === w.id ? (
                        <div style={{ display: 'flex', gap: 4 }} onClick={(e) => e.stopPropagation()}>
                          <button
                            onClick={() => handleDelete(w.id)}
                            style={{
                              background: 'var(--danger)', color: 'white', border: 'none',
                              borderRadius: 6, padding: '2px 8px', fontSize: 12, cursor: 'pointer',
                            }}
                            aria-label="Подтвердить удаление"
                          >Да</button>
                          <button
                            onClick={() => setConfirmId(null)}
                            style={{
                              background: 'var(--bg-secondary)', color: 'var(--text-secondary)', border: 'none',
                              borderRadius: 6, padding: '2px 8px', fontSize: 12, cursor: 'pointer',
                            }}
                            aria-label="Отменить удаление"
                          >Нет</button>
                        </div>
                      ) : (
                        <button
                          onClick={(e) => { e.stopPropagation(); setConfirmId(w.id); }}
                          style={{
                            background: 'none', border: 'none', color: 'var(--text-muted)',
                            cursor: 'pointer', padding: '0 4px', fontSize: 16, lineHeight: 1,
                          }}
                          aria-label={`Удалить тренировку за ${w.date}`}
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

                {/* Expandable details */}
                {isExpanded && (
                  <div style={{
                    marginTop: 8,
                    paddingTop: 8,
                    borderTop: '1px solid var(--border-color, rgba(255,255,255,0.08))',
                  }}>
                    {isLoadingThis ? (
                      <div style={{ textAlign: 'center', padding: '8px 0', fontSize: 13, color: 'var(--text-muted)' }}>
                        Загрузка...
                      </div>
                    ) : wDetails && wDetails.sets.length > 0 ? (
                      groupSetsByExercise(wDetails.sets).map((group, gi) => (
                        <div key={gi} style={{ marginBottom: gi < groupSetsByExercise(wDetails.sets).length - 1 ? 10 : 0 }}>
                          <div style={{
                            fontSize: 13, fontWeight: 600, color: 'var(--workout-accent)',
                            marginBottom: 4,
                          }}>
                            {group.name}
                          </div>
                          {group.sets.map((s, si) => (
                            <div key={si} style={{
                              display: 'flex', alignItems: 'center', gap: 8,
                              fontSize: 13, color: 'var(--text-secondary)',
                              padding: '2px 0 2px 12px',
                            }}>
                              <span style={{
                                width: 18, height: 18, borderRadius: '50%',
                                background: 'var(--bg-secondary)', display: 'flex',
                                alignItems: 'center', justifyContent: 'center',
                                fontSize: 11, fontWeight: 600, flexShrink: 0,
                              }}>
                                {s.set_number}
                              </span>
                              <span style={{ fontWeight: 500 }}>{s.weight} кг</span>
                              <span>× {s.reps}</span>
                              {s.rpe ? <span style={{ color: 'var(--text-muted)', fontSize: 11 }}>RPE {s.rpe}</span> : null}
                              {s.notes ? <span style={{ color: 'var(--text-muted)', fontSize: 11, fontStyle: 'italic' }}>{s.notes}</span> : null}
                            </div>
                          ))}
                        </div>
                      ))
                    ) : (
                      <div style={{ fontSize: 13, color: 'var(--text-muted)', textAlign: 'center', padding: '4px 0' }}>
                        Нет записей о подходах
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
