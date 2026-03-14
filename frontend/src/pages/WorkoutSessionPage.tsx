import { useState, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  getNextWorkout, createWorkout, addWorkoutSet, completeWorkout, getWorkout,
} from '../api/client';
import type { WorkoutCreate, WorkoutDetail, Exercise } from '../types';
import PreWorkoutForm from '../components/workout/PreWorkoutForm';
import WarmupPhase from '../components/workout/WarmupPhase';
import SetInput from '../components/workout/SetInput';
import RPESelector from '../components/workout/RPESelector';
import RestTimer from '../components/workout/RestTimer';
import WorkoutSummary from '../components/workout/WorkoutSummary';

type Phase = 'loading' | 'pre' | 'warmup' | 'exercise' | 'rpe' | 'rest' | 'summary';

export default function WorkoutSessionPage() {
  const navigate = useNavigate();
  const [phase, setPhase] = useState<Phase>('loading');
  const [dayType, setDayType] = useState('A');
  const [exercises, setExercises] = useState<Exercise[]>([]);
  const [workout, setWorkout] = useState<WorkoutDetail | null>(null);
  const [exIndex, setExIndex] = useState(0);
  const [setNumber, setSetNumber] = useState(1);
  const [lastWeight, setLastWeight] = useState(0);
  const [lastReps, setLastReps] = useState(0);

  useEffect(() => {
    getNextWorkout().then((data) => {
      setDayType(data.next_day);
      setExercises(data.exercises);
      setPhase('pre');
    }).catch(() => setPhase('pre'));
  }, []);

  const handlePreSubmit = async (data: WorkoutCreate) => {
    try {
      const w = await createWorkout(data);
      setWorkout(w);
      setPhase('warmup');
    } catch {
      window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('error');
    }
  };

  const handleSetSubmit = (weight: number, reps: number) => {
    setLastWeight(weight);
    setLastReps(reps);
    window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('medium');
    setPhase('rpe');
  };

  const handleRPE = async (rpe: number) => {
    if (!workout) return;
    const ex = exercises[exIndex];
    try {
      await addWorkoutSet(workout.id, {
        exercise_id: ex.exercise_id,
        set_number: setNumber,
        weight: lastWeight,
        reps: lastReps,
        rpe,
      });

      const defaultSets = ex.default_sets || 3;
      if (setNumber < defaultSets) {
        setSetNumber(setNumber + 1);
        setPhase('rest');
      } else {
        // Следующее упражнение
        if (exIndex < exercises.length - 1) {
          setExIndex(exIndex + 1);
          setSetNumber(1);
          setPhase('rest');
        } else {
          // Все упражнения завершены
          const updated = await getWorkout(workout.id);
          setWorkout(updated);
          setPhase('summary');
        }
      }
    } catch {
      window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('error');
    }
  };

  const handleRestComplete = useCallback(() => {
    setPhase('exercise');
  }, []);

  const handleComplete = async (energyAfter: number, notes: string) => {
    if (!workout) return;
    try {
      await completeWorkout(workout.id, { energy_after: energyAfter, notes: notes || undefined });
      window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('success');
      navigate('/workouts');
    } catch {
      window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('error');
    }
  };

  if (phase === 'loading') {
    return <div className="page"><div className="loading">Загрузка...</div></div>;
  }

  const currentExercise = exercises[exIndex];

  return (
    <div className="page">
      {phase !== 'rest' && (
        <h1 className="page-title">
          Тренировка · День {dayType}
          {phase === 'exercise' && currentExercise && (
            <span className="stat-label" style={{ display: 'block', fontSize: 13, fontWeight: 400 }}>
              {exIndex + 1}/{exercises.length} · {currentExercise.name}
            </span>
          )}
        </h1>
      )}

      {phase === 'pre' && (
        <PreWorkoutForm dayType={dayType} onSubmit={handlePreSubmit} />
      )}

      {phase === 'warmup' && (
        <WarmupPhase onComplete={() => setPhase('exercise')} />
      )}

      {phase === 'exercise' && currentExercise && (
        <SetInput
          exerciseName={currentExercise.name}
          setNumber={setNumber}
          defaultWeight={currentExercise.current_weight || 0}
          weightStep={currentExercise.weight_step}
          targetReps={currentExercise.target_reps || `${currentExercise.reps_min || 8}-${currentExercise.reps_max || 12}`}
          onSubmit={handleSetSubmit}
        />
      )}

      {phase === 'rpe' && (
        <RPESelector onSelect={handleRPE} />
      )}

      {phase === 'rest' && currentExercise && (
        <RestTimer
          seconds={currentExercise.rest_seconds || 90}
          onComplete={handleRestComplete}
          onSkip={handleRestComplete}
        />
      )}

      {phase === 'summary' && workout && (
        <WorkoutSummary workout={workout} onComplete={handleComplete} />
      )}
    </div>
  );
}
