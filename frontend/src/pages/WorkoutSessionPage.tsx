import { useEffect, useState, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTelegram } from '../hooks/useTelegram';
import {
  getNextWorkoutFull, createWorkout, addWorkoutSet, completeWorkout,
} from '../api/client';
import type {
  NextWorkoutFull, ExerciseWithDetails, WorkoutFull,
} from '../types';
import '../styles/workout-session.css';

// ---- Types ----
type Stage = 'loading' | 'pre' | 'warmup' | 'exercise' | 'rest' | 'post' | 'summary';

interface PreWorkoutData {
  energy_before: number;
  sleep_hours: number;
  sleep_quality: number;
  back_pain: number;
  emotional_wave: string;
}

interface SetEntry {
  weight: number;
  reps: number;
  rpe: number;
}

const WARMUP_PHASES = [
  {
    id: 1, title: 'Общая активация',
    desc: 'Быстрая ходьба или велотренажёр — 3 минуты',
    icon: '🫀',
  },
  {
    id: 2, title: 'Подготовка к движению',
    desc: 'Присед без веса 10x (пауза 3 сек), Кошка-корова 10x, Ягодичный мостик 15x',
    icon: '🔄',
  },
  {
    id: 3, title: 'Специфическая разминка',
    desc: '1 подход каждого упражнения с 50% рабочего веса',
    icon: '🎯',
  },
];

const STORAGE_KEY = 'workout_session';

// ---- Helpers ----
function saveSession(data: Record<string, unknown>) {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(data)); } catch { /* */ }
}
function loadSession(): Record<string, unknown> | null {
  try {
    const s = localStorage.getItem(STORAGE_KEY);
    return s ? JSON.parse(s) : null;
  } catch { return null; }
}
function clearSession() {
  localStorage.removeItem(STORAGE_KEY);
}

export default function WorkoutSessionPage() {
  const navigate = useNavigate();
  const { haptic } = useTelegram();

  // Core state
  const [stage, setStage] = useState<Stage>('loading');
  const [plan, setPlan] = useState<NextWorkoutFull | null>(null);
  const [workoutId, setWorkoutId] = useState<number | null>(null);
  const [error, setError] = useState('');

  // Pre-workout
  const [pre, setPre] = useState<PreWorkoutData>({
    energy_before: 7, sleep_hours: 7, sleep_quality: 7, back_pain: 1, emotional_wave: '',
  });
  const [preStep, setPreStep] = useState(0); // 0-4

  // Warmup
  const [warmupDone, setWarmupDone] = useState<boolean[]>([false, false, false]);

  // Exercise
  const [exIdx, setExIdx] = useState(0);
  const [setNum, setSetNum] = useState(1);
  const [setWeight, setSetWeight] = useState(0);
  const [setReps, setSetReps] = useState(0);
  const [, setSetRpe] = useState(0);
  const [setsLog, setSetsLog] = useState<Record<string, SetEntry[]>>({});
  const [showRpe, setShowRpe] = useState(false);
  const [saving, setSaving] = useState(false);

  // Rest timer
  const [restTotal, setRestTotal] = useState(90);
  const [restLeft, setRestLeft] = useState(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Post-workout
  const [energyAfter, setEnergyAfter] = useState(7);
  const [workoutNotes, setWorkoutNotes] = useState('');

  // Summary
  const [summaryData, setSummaryData] = useState<WorkoutFull | null>(null);
  const [showConfetti, setShowConfetti] = useState(false);

  // ---- Load plan ----
  useEffect(() => {
    // Check for saved session
    const saved = loadSession();
    if (saved && saved.workoutId && saved.plan) {
      setPlan(saved.plan as NextWorkoutFull);
      setWorkoutId(saved.workoutId as number);
      setExIdx((saved.exIdx as number) || 0);
      setSetNum((saved.setNum as number) || 1);
      setSetsLog((saved.setsLog as Record<string, SetEntry[]>) || {});
      setWarmupDone((saved.warmupDone as boolean[]) || [false, false, false]);
      setStage('exercise');
      return;
    }

    getNextWorkoutFull()
      .then((data) => {
        setPlan(data);
        setStage('pre');
      })
      .catch((e) => setError(e.message));
  }, []);

  // ---- Auto-save ----
  useEffect(() => {
    if (workoutId && plan && stage === 'exercise') {
      saveSession({ workoutId, plan, exIdx, setNum, setsLog, warmupDone });
    }
  }, [workoutId, exIdx, setNum, setsLog, stage]);

  // ---- Current exercise ----
  const exercises = plan?.exercises || [];
  const currentEx = exercises[exIdx] as ExerciseWithDetails | undefined;
  const totalExercises = exercises.length;

  // ---- Progress calculation ----
  const getProgress = (): number => {
    if (stage === 'loading') return 0;
    if (stage === 'pre') return 5 + preStep * 3;
    if (stage === 'warmup') return 20;
    if (stage === 'exercise' || stage === 'rest') {
      const base = 25;
      const exRange = 65;
      if (totalExercises === 0) return base;
      return base + (exIdx / totalExercises) * exRange;
    }
    if (stage === 'post') return 92;
    return 100;
  };

  // ---- Pre-workout handlers ----
  const preLabels = ['Энергия', 'Часы сна', 'Качество сна', 'Боль в спине', 'Эмоц. волна'];

  const handlePreNext = async () => {
    haptic?.selectionChanged();
    if (preStep < 4) {
      setPreStep(preStep + 1);
      return;
    }
    // All pre-workout data collected — create workout
    if (!plan) return;
    setSaving(true);
    try {
      const result = await createWorkout({
        day_type: plan.next_day,
        week: plan.phase.current_week,
        phase: plan.phase.phase_name,
        ...pre,
      });
      setWorkoutId(result.id);
      setStage('warmup');
    } catch (e: unknown) {
      setError((e as Error).message);
    } finally {
      setSaving(false);
    }
  };

  const handlePreBack = () => {
    if (preStep > 0) setPreStep(preStep - 1);
  };

  // ---- Warmup handlers ----
  const toggleWarmup = (idx: number) => {
    haptic?.selectionChanged();
    setWarmupDone(prev => {
      const next = [...prev];
      next[idx] = !next[idx];
      return next;
    });
  };

  const handleWarmupDone = () => {
    haptic?.notificationOccurred('success');
    if (currentEx) {
      setSetWeight(currentEx.current_weight || 0);
      setSetReps(currentEx.reps_max || 10);
    }
    setStage('exercise');
  };

  // ---- Exercise handlers ----
  const initExercise = useCallback((idx: number) => {
    const ex = exercises[idx] as ExerciseWithDetails | undefined;
    if (ex) {
      setSetWeight(ex.current_weight || 0);
      setSetReps(ex.reps_max || 10);
      setSetNum((setsLog[ex.exercise_id]?.length || 0) + 1);
      setSetRpe(0);
      setShowRpe(false);
    }
  }, [exercises, setsLog]);

  useEffect(() => {
    if (stage === 'exercise' && currentEx) {
      const existing = setsLog[currentEx.exercise_id];
      if (!existing || existing.length === 0) {
        setSetWeight(currentEx.current_weight || 0);
        setSetReps(currentEx.reps_max || 10);
      }
    }
  }, [exIdx, stage]);

  const handleSetDone = () => {
    setShowRpe(true);
    haptic?.impactOccurred('medium');
  };

  const handleRpeSelect = async (rpe: number) => {
    if (!workoutId || !currentEx) return;
    setSetRpe(rpe);
    setSaving(true);
    haptic?.notificationOccurred('success');

    try {
      await addWorkoutSet(workoutId, {
        exercise_id: currentEx.exercise_id,
        set_number: setNum,
        weight: setWeight,
        reps: setReps,
        rpe,
      });

      const entry: SetEntry = { weight: setWeight, reps: setReps, rpe };
      setSetsLog(prev => ({
        ...prev,
        [currentEx.exercise_id]: [...(prev[currentEx.exercise_id] || []), entry],
      }));

      setShowRpe(false);
      const targetSets = currentEx.default_sets || 3;
      if (setNum >= targetSets) {
        // Exercise complete — next exercise or post
        if (exIdx < totalExercises - 1) {
          const nextIdx = exIdx + 1;
          setExIdx(nextIdx);
          initExercise(nextIdx);
        } else {
          setStage('post');
        }
      } else {
        // Start rest timer
        setRestTotal(currentEx.rest_seconds || 90);
        setRestLeft(currentEx.rest_seconds || 90);
        setSetNum(setNum + 1);
        setStage('rest');
      }
    } catch (e: unknown) {
      setError((e as Error).message);
    } finally {
      setSaving(false);
    }
  };

  const handleSkipExercise = () => {
    haptic?.selectionChanged();
    if (exIdx < totalExercises - 1) {
      const nextIdx = exIdx + 1;
      setExIdx(nextIdx);
      initExercise(nextIdx);
    } else {
      setStage('post');
    }
  };

  const handleFinishEarly = () => {
    haptic?.selectionChanged();
    setStage('post');
  };

  // ---- Rest timer ----
  useEffect(() => {
    if (stage === 'rest' && restLeft > 0) {
      timerRef.current = setInterval(() => {
        setRestLeft(prev => {
          if (prev <= 1) {
            clearInterval(timerRef.current!);
            haptic?.notificationOccurred('warning');
            setStage('exercise');
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [stage, restTotal]);

  const handleTimerSkip = () => {
    if (timerRef.current) clearInterval(timerRef.current);
    setRestLeft(0);
    haptic?.selectionChanged();
    setStage('exercise');
  };

  const handleTimerAdd30 = () => {
    setRestLeft(prev => prev + 30);
    haptic?.selectionChanged();
  };

  // ---- Post-workout ----
  const handleComplete = async () => {
    if (!workoutId) return;
    setSaving(true);
    haptic?.notificationOccurred('success');
    try {
      const result = await completeWorkout(workoutId, energyAfter, workoutNotes || undefined);
      setSummaryData(result);
      clearSession();

      // Check for progress
      const hasProgress = result.progress_updates?.some(p => p.status === 'ready');
      if (hasProgress) {
        setShowConfetti(true);
        setTimeout(() => setShowConfetti(false), 3000);
      }

      setStage('summary');
    } catch (e: unknown) {
      setError((e as Error).message);
    } finally {
      setSaving(false);
    }
  };

  // ---- Render helpers ----
  const renderSlider = (
    value: number, min: number, max: number, step: number,
    onChange: (v: number) => void, label: string, color?: string,
  ) => (
    <div className="ws-slider-group">
      <div className="ws-slider-label">
        <span>{label}</span>
        <span className="ws-slider-value" style={{ color }}>{value}</span>
      </div>
      <input
        type="range" min={min} max={max} step={step} value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="ws-slider"
      />
      <div className="ws-slider-range">
        <span>{min}</span><span>{max}</span>
      </div>
    </div>
  );

  // ---- Timer circle ----
  const renderTimerCircle = () => {
    const pct = restTotal > 0 ? restLeft / restTotal : 0;
    const r = 80;
    const circ = 2 * Math.PI * r;
    const offset = circ * (1 - pct);
    const mins = Math.floor(restLeft / 60);
    const secs = restLeft % 60;

    return (
      <div className="ws-timer-container">
        <svg width="200" height="200" viewBox="0 0 200 200">
          <circle cx="100" cy="100" r={r} fill="none" stroke="var(--border)" strokeWidth="8" />
          <circle
            cx="100" cy="100" r={r} fill="none"
            stroke="var(--accent)" strokeWidth="8" strokeLinecap="round"
            strokeDasharray={circ} strokeDashoffset={offset}
            transform="rotate(-90 100 100)"
            style={{ transition: 'stroke-dashoffset 1s linear' }}
          />
        </svg>
        <div className="ws-timer-text">
          {mins}:{secs.toString().padStart(2, '0')}
        </div>
      </div>
    );
  };

  // ---- Error state ----
  if (error) return (
    <div className="page ws-page">
      <div className="error-box">
        <div className="error-icon">&#x26A0;&#xFE0F;</div>
        <div className="error-text">{error}</div>
        <button className="btn btn-primary" onClick={() => { setError(''); navigate('/workouts'); }}>
          Назад
        </button>
      </div>
    </div>
  );

  // ---- Loading ----
  if (stage === 'loading') return (
    <div className="page ws-page">
      <div className="loading">Загрузка тренировки...</div>
    </div>
  );

  return (
    <div className="page ws-page">
      {/* Progress bar */}
      <div className="ws-progress-bar">
        <div className="ws-progress-fill" style={{ width: `${getProgress()}%` }} />
      </div>

      {/* Confetti overlay */}
      {showConfetti && (
        <div className="ws-confetti">
          {Array.from({ length: 30 }).map((_, i) => (
            <div
              key={i}
              className="ws-confetti-piece"
              style={{
                left: `${Math.random() * 100}%`,
                animationDelay: `${Math.random() * 0.5}s`,
                backgroundColor: ['#22c55e', '#3b82f6', '#f59e0b', '#ef4444', '#a855f7'][i % 5],
              }}
            />
          ))}
        </div>
      )}

      {/* ==================== PRE-WORKOUT ==================== */}
      {stage === 'pre' && plan && (
        <div className="ws-stage">
          <div className="ws-header">
            <h2>День {plan.next_day}</h2>
            <p className="ws-meta">
              {plan.phase.phase_name} &middot; Неделя {plan.phase.current_week} &middot; RPE {plan.phase.rpe_min}-{plan.phase.rpe_max}
            </p>
          </div>

          <div className="ws-step-indicator">
            {preLabels.map((_, i) => (
              <div key={i} className={`ws-step-dot ${i <= preStep ? 'active' : ''}`} />
            ))}
          </div>

          {preStep === 0 && (
            <div className="ws-card">
              <h3>Энергия</h3>
              <p className="ws-hint">Как ты себя чувствуешь?</p>
              {renderSlider(pre.energy_before, 1, 10, 1,
                (v) => setPre({ ...pre, energy_before: v }), 'Энергия',
                pre.energy_before <= 4 ? 'var(--danger)' : pre.energy_before >= 7 ? 'var(--success)' : 'var(--warning)'
              )}
              {pre.energy_before <= 4 && (
                <div className="ws-warning">
                  Низкая энергия. Как Проектор, подумай — стоит ли тренироваться сегодня?
                  Можно сократить объём или перенести.
                </div>
              )}
            </div>
          )}

          {preStep === 1 && (
            <div className="ws-card">
              <h3>Сон</h3>
              <p className="ws-hint">Сколько часов спал?</p>
              {renderSlider(pre.sleep_hours, 3, 12, 0.5,
                (v) => setPre({ ...pre, sleep_hours: v }), 'Часы сна',
                pre.sleep_hours < 6 ? 'var(--danger)' : pre.sleep_hours >= 7 ? 'var(--success)' : 'var(--warning)'
              )}
            </div>
          )}

          {preStep === 2 && (
            <div className="ws-card">
              <h3>Качество сна</h3>
              <p className="ws-hint">Как выспался?</p>
              {renderSlider(pre.sleep_quality, 1, 10, 1,
                (v) => setPre({ ...pre, sleep_quality: v }), 'Качество')}
            </div>
          )}

          {preStep === 3 && (
            <div className="ws-card">
              <h3>Боль в спине</h3>
              <p className="ws-hint">0 = нет боли</p>
              {renderSlider(pre.back_pain, 1, 10, 1,
                (v) => setPre({ ...pre, back_pain: v }), 'Боль',
                pre.back_pain >= 6 ? 'var(--danger)' : 'var(--success)'
              )}
              {pre.back_pain >= 6 && (
                <div className="ws-warning">
                  Высокая боль в спине. Исключи осевую нагрузку,
                  делай McGill Big 3 особенно внимательно.
                </div>
              )}
            </div>
          )}

          {preStep === 4 && (
            <div className="ws-card">
              <h3>Эмоциональная волна</h3>
              <p className="ws-hint">Как настроение сейчас?</p>
              <div className="ws-wave-buttons">
                {[
                  { val: 'up', icon: '📈', label: 'На подъёме' },
                  { val: 'neutral', icon: '➡️', label: 'Нейтрально' },
                  { val: 'down', icon: '📉', label: 'На спаде' },
                ].map(w => (
                  <button
                    key={w.val}
                    className={`ws-wave-btn ${pre.emotional_wave === w.val ? 'active' : ''}`}
                    onClick={() => { setPre({ ...pre, emotional_wave: w.val }); haptic?.selectionChanged(); }}
                  >
                    <span className="ws-wave-icon">{w.icon}</span>
                    <span>{w.label}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className="ws-actions">
            {preStep > 0 && (
              <button className="btn btn-ghost" onClick={handlePreBack}>Назад</button>
            )}
            <button
              className="btn btn-primary"
              style={{ flex: 1 }}
              disabled={saving || (preStep === 4 && !pre.emotional_wave)}
              onClick={handlePreNext}
            >
              {saving ? 'Создаю...' : preStep < 4 ? 'Далее' : 'Начать разминку'}
            </button>
          </div>
        </div>
      )}

      {/* ==================== WARMUP ==================== */}
      {stage === 'warmup' && (
        <div className="ws-stage">
          <div className="ws-header">
            <h2>Разминка</h2>
            <p className="ws-meta">{warmupDone.filter(Boolean).length}/3 фаз выполнено</p>
          </div>

          {WARMUP_PHASES.map((phase, i) => (
            <button
              key={phase.id}
              className={`ws-warmup-item ${warmupDone[i] ? 'done' : ''}`}
              onClick={() => toggleWarmup(i)}
            >
              <span className="ws-warmup-check">
                {warmupDone[i] ? '✅' : '⬜'}
              </span>
              <div className="ws-warmup-content">
                <div className="ws-warmup-title">
                  <span>{phase.icon}</span> {phase.title}
                </div>
                <div className="ws-warmup-desc">{phase.desc}</div>
              </div>
            </button>
          ))}

          <div className="ws-actions">
            <button className="btn btn-ghost" onClick={handleWarmupDone}>
              Пропустить
            </button>
            <button className="btn btn-primary" style={{ flex: 1 }} onClick={handleWarmupDone}>
              Перейти к упражнениям
            </button>
          </div>
        </div>
      )}

      {/* ==================== EXERCISE ==================== */}
      {stage === 'exercise' && currentEx && (
        <div className="ws-stage">
          <div className="ws-header">
            <div className="ws-ex-counter">{exIdx + 1} / {totalExercises}</div>
            <h2>{currentEx.name}</h2>
            <p className="ws-meta">{currentEx.category}</p>
          </div>

          {/* Technical notes */}
          {currentEx.notes && (
            <div className="ws-card ws-ex-notes">
              <span className="ws-notes-icon">💡</span> {currentEx.notes}
            </div>
          )}

          {/* Exercise info card */}
          <div className="ws-card ws-ex-info">
            <div className="ws-ex-stats">
              <div className="ws-ex-stat">
                <span className="ws-ex-stat-val">{currentEx.current_weight || 0}</span>
                <span className="ws-ex-stat-label">кг</span>
              </div>
              <div className="ws-ex-stat">
                <span className="ws-ex-stat-val">{currentEx.reps_min}-{currentEx.reps_max}</span>
                <span className="ws-ex-stat-label">повтор.</span>
              </div>
              <div className="ws-ex-stat">
                <span className="ws-ex-stat-val">{currentEx.default_sets || 3}</span>
                <span className="ws-ex-stat-label">подходов</span>
              </div>
              <div className="ws-ex-stat">
                <span className="ws-ex-stat-val">{plan?.phase.rpe_min}-{plan?.phase.rpe_max}</span>
                <span className="ws-ex-stat-label">RPE</span>
              </div>
            </div>
          </div>

          {/* Previous sets for this exercise */}
          {(setsLog[currentEx.exercise_id]?.length ?? 0) > 0 && (
            <div className="ws-card">
              <div className="ws-card-title">Сегодня</div>
              <div className="ws-sets-log">
                {setsLog[currentEx.exercise_id].map((s, i) => (
                  <div key={i} className="ws-set-row">
                    <span className="ws-set-num">#{i + 1}</span>
                    <span>{s.weight} кг</span>
                    <span>x {s.reps}</span>
                    <span className="ws-set-rpe">RPE {s.rpe}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Last workout history */}
          {currentEx.history && currentEx.history.length > 0 && (
            <div className="ws-card">
              <div className="ws-card-title">Прошлые тренировки</div>
              {currentEx.history.slice(0, 2).map((h, i) => (
                <div key={i} className="ws-history-row">
                  <span className="ws-history-date">{h.date}</span>
                  <span className="ws-history-sets">
                    {h.sets.map(s => `${s.weight}x${s.reps}`).join(', ')}
                  </span>
                </div>
              ))}
            </div>
          )}

          {/* Set input */}
          {!showRpe ? (
            <div className="ws-card ws-set-input">
              <div className="ws-card-title">
                Подход {setNum} / {currentEx.default_sets || 3}
              </div>

              {/* Weight input */}
              <div className="ws-input-row">
                <span className="ws-input-label">Вес (кг)</span>
                <div className="ws-input-control">
                  <button className="ws-adj-btn" onClick={() => { setSetWeight(Math.max(0, setWeight - (currentEx.weight_step || 2.5))); haptic?.selectionChanged(); }}>
                    -{currentEx.weight_step || 2.5}
                  </button>
                  <input
                    type="number" inputMode="decimal"
                    className="ws-weight-input"
                    value={setWeight}
                    onChange={(e) => setSetWeight(Number(e.target.value))}
                  />
                  <button className="ws-adj-btn" onClick={() => { setSetWeight(setWeight + (currentEx.weight_step || 2.5)); haptic?.selectionChanged(); }}>
                    +{currentEx.weight_step || 2.5}
                  </button>
                </div>
              </div>

              {/* Reps input */}
              <div className="ws-input-row">
                <span className="ws-input-label">Повторения</span>
                <div className="ws-input-control">
                  <button className="ws-adj-btn" onClick={() => { setSetReps(Math.max(1, setReps - 1)); haptic?.selectionChanged(); }}>
                    -1
                  </button>
                  <input
                    type="number" inputMode="numeric"
                    className="ws-weight-input"
                    value={setReps}
                    onChange={(e) => setSetReps(Number(e.target.value))}
                  />
                  <button className="ws-adj-btn" onClick={() => { setSetReps(setReps + 1); haptic?.selectionChanged(); }}>
                    +1
                  </button>
                </div>
              </div>

              <button
                className="btn btn-primary btn-full"
                onClick={handleSetDone}
                disabled={setWeight <= 0 || setReps <= 0}
              >
                Подход завершён
              </button>
            </div>
          ) : (
            /* RPE selector */
            <div className="ws-card">
              <div className="ws-card-title">
                {setWeight} кг x {setReps} — Насколько тяжело?
              </div>
              <div className="ws-rpe-grid">
                {[5, 6, 7, 8, 9, 10].map(r => (
                  <button
                    key={r}
                    className={`ws-rpe-btn ${r <= 7 ? 'easy' : r <= 8 ? 'medium' : 'hard'}`}
                    onClick={() => handleRpeSelect(r)}
                    disabled={saving}
                  >
                    <span className="ws-rpe-num">{r}</span>
                    <span className="ws-rpe-desc">
                      {r === 5 ? 'Легко' : r === 6 ? 'Умеренно' : r === 7 ? 'Норм' :
                       r === 8 ? 'Тяжело' : r === 9 ? 'Очень' : 'Макс'}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Exercise actions */}
          <div className="ws-actions">
            <button className="btn btn-ghost" onClick={handleSkipExercise}>
              Пропустить
            </button>
            <button className="btn btn-ghost" onClick={handleFinishEarly}>
              Завершить
            </button>
          </div>
        </div>
      )}

      {/* ==================== REST TIMER ==================== */}
      {stage === 'rest' && (
        <div className="ws-stage ws-rest-stage">
          <div className="ws-header">
            <h2>Отдых</h2>
            <p className="ws-meta">Следующий подход #{setNum}</p>
          </div>

          {renderTimerCircle()}

          <div className="ws-actions" style={{ marginTop: 24 }}>
            <button className="btn btn-ghost" onClick={handleTimerAdd30}>
              +30 сек
            </button>
            <button className="btn btn-primary" style={{ flex: 1 }} onClick={handleTimerSkip}>
              Готов раньше
            </button>
          </div>
        </div>
      )}

      {/* ==================== POST-WORKOUT ==================== */}
      {stage === 'post' && (
        <div className="ws-stage">
          <div className="ws-header">
            <h2>Тренировка окончена!</h2>
            <p className="ws-meta">Осталось оценить самочувствие</p>
          </div>

          <div className="ws-card">
            <h3>Энергия после</h3>
            {renderSlider(energyAfter, 1, 10, 1,
              setEnergyAfter, 'Энергия',
              energyAfter <= 3 ? 'var(--danger)' : energyAfter >= 7 ? 'var(--success)' : 'var(--warning)'
            )}
          </div>

          <div className="ws-card">
            <h3>Заметки (необязательно)</h3>
            <textarea
              className="ws-notes"
              placeholder="Как прошла тренировка..."
              value={workoutNotes}
              onChange={(e) => setWorkoutNotes(e.target.value)}
              rows={3}
            />
          </div>

          <button
            className="btn btn-primary btn-full"
            onClick={handleComplete}
            disabled={saving}
            style={{ padding: '14px 0', fontSize: 16 }}
          >
            {saving ? 'Сохраняю...' : 'Завершить тренировку'}
          </button>
        </div>
      )}

      {/* ==================== SUMMARY ==================== */}
      {stage === 'summary' && summaryData && (
        <div className="ws-stage">
          <div className="ws-header">
            <h2>Тренировка #{summaryData.id}</h2>
            <p className="ws-meta">
              День {summaryData.day_type} &middot; {summaryData.phase} &middot; Неделя {summaryData.week}
            </p>
          </div>

          {/* Energy change */}
          <div className="ws-card">
            <div className="ws-summary-energy">
              <div className="ws-energy-block">
                <span className="ws-energy-val">{summaryData.energy_before}</span>
                <span className="ws-energy-label">До</span>
              </div>
              <span className="ws-energy-arrow">
                {(summaryData.energy_after ?? 0) > (summaryData.energy_before ?? 0) ? '📈' :
                 (summaryData.energy_after ?? 0) < (summaryData.energy_before ?? 0) ? '📉' : '➡️'}
              </span>
              <div className="ws-energy-block">
                <span className="ws-energy-val">{summaryData.energy_after}</span>
                <span className="ws-energy-label">После</span>
              </div>
            </div>
            {((summaryData.energy_before ?? 0) - (summaryData.energy_after ?? 0)) > 3 && (
              <div className="ws-warning">
                Энергия упала на {(summaryData.energy_before ?? 0) - (summaryData.energy_after ?? 0)} пунктов.
                Как Проектор, 48-72ч до следующей тренировки!
              </div>
            )}
          </div>

          {/* Stats */}
          <div className="ws-card">
            <div className="ws-card-title">Статистика</div>
            <div className="ws-summary-stats">
              <div className="ws-summary-stat">
                <span className="ws-summary-val">{Object.keys(setsLog).length}</span>
                <span className="ws-summary-label">Упражнений</span>
              </div>
              <div className="ws-summary-stat">
                <span className="ws-summary-val">
                  {Object.values(setsLog).reduce((a, b) => a + b.length, 0)}
                </span>
                <span className="ws-summary-label">Подходов</span>
              </div>
              <div className="ws-summary-stat">
                <span className="ws-summary-val">
                  {Object.values(setsLog).reduce(
                    (a, b) => a + b.reduce((x, y) => x + y.weight * y.reps, 0), 0
                  ).toFixed(0)}
                </span>
                <span className="ws-summary-label">Объём (кг)</span>
              </div>
            </div>
          </div>

          {/* Exercise details */}
          <div className="ws-card">
            <div className="ws-card-title">По упражнениям</div>
            {exercises.map(ex => {
              const sets = setsLog[ex.exercise_id];
              if (!sets || sets.length === 0) return null;
              const avgRpe = sets.reduce((a, b) => a + b.rpe, 0) / sets.length;
              return (
                <div key={ex.exercise_id} className="ws-summary-exercise">
                  <div className="ws-summary-ex-name">{ex.name}</div>
                  <div className="ws-summary-ex-detail">
                    {sets.map((s) => `${s.weight}x${s.reps}`).join(' | ')}
                    <span className="ws-summary-ex-rpe">RPE {avgRpe.toFixed(1)}</span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Progress updates */}
          {summaryData.progress_updates && summaryData.progress_updates.length > 0 && (
            <div className="ws-card">
              <div className="ws-card-title">Прогресс</div>
              {summaryData.progress_updates.map(p => (
                <div key={p.exercise_id} className={`ws-progress-item ${p.status === 'ready' ? 'ready' : ''}`}>
                  <span>{exercises.find(e => e.exercise_id === p.exercise_id)?.name || p.exercise_id}</span>
                  <span>
                    {p.status === 'ready'
                      ? `🎉 Готов к +${p.weight_step} кг!`
                      : `${p.weight} кг · RPE ${p.avg_rpe}`
                    }
                  </span>
                </div>
              ))}
            </div>
          )}

          {/* Muscle groups */}
          <div className="ws-card">
            <div className="ws-card-title">Нагрузка по группам мышц</div>
            <div className="ws-muscle-groups">
              {Object.entries(
                exercises.reduce<Record<string, number>>((acc, ex) => {
                  const sets = setsLog[ex.exercise_id];
                  if (sets) {
                    const cat = (ex as ExerciseWithDetails).category || 'Другое';
                    acc[cat] = (acc[cat] || 0) + sets.reduce((a, s) => a + s.weight * s.reps, 0);
                  }
                  return acc;
                }, {})
              ).map(([cat, vol]) => (
                <div key={cat} className="ws-muscle-row">
                  <span>{cat}</span>
                  <span className="amount">{vol.toFixed(0)} кг</span>
                </div>
              ))}
            </div>
          </div>

          <button
            className="btn btn-primary btn-full"
            onClick={() => navigate('/workouts')}
            style={{ padding: '14px 0', fontSize: 16, marginTop: 8 }}
          >
            Готово
          </button>
        </div>
      )}
    </div>
  );
}
