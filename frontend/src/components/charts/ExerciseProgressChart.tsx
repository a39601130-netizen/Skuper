import { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip } from 'recharts';
import { getExerciseProgress } from '../../api/client';

interface Props {
  exerciseId: string;
  exerciseName: string;
}

export default function ExerciseProgressChart({ exerciseId, exerciseName }: Props) {
  const [data, setData] = useState<{ date: string; weight: number }[]>([]);

  useEffect(() => {
    getExerciseProgress(exerciseId).then((result) => {
      const history = (result as { history_by_workout?: { date?: string; sets: { weight: number }[] }[] })
        .history_by_workout || [];
      const chartData = history
        .filter((h) => h.date)
        .map((h) => ({
          date: (h.date || '').slice(5),
          weight: Math.max(...h.sets.map((s) => s.weight)),
        }))
        .reverse();
      setData(chartData);
    }).catch(() => {});
  }, [exerciseId]);

  if (data.length < 2) return null;

  return (
    <div className="card">
      <div className="card-title">{exerciseName}</div>
      <ResponsiveContainer width="100%" height={120}>
        <LineChart data={data}>
          <XAxis dataKey="date" tick={{ fontSize: 10, fill: 'var(--text-secondary)' }} />
          <YAxis tick={{ fontSize: 10, fill: 'var(--text-secondary)' }} width={35} />
          <Tooltip
            contentStyle={{
              background: 'var(--bg-card)', border: '1px solid var(--border)',
              borderRadius: 8, fontSize: 12,
            }}
          />
          <Line type="monotone" dataKey="weight" stroke="#34d399" strokeWidth={2} dot={{ r: 3 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
